"""PDF to Markdown & RAG chunks (with OCR) - Apify Actor."""
from __future__ import annotations

import asyncio
import hashlib
import re
from datetime import datetime, timezone
from urllib.parse import unquote, urlparse

import httpx
import pymupdf
import pymupdf4llm
from apify import Actor

from .chunking import chunk_pages
from .threads import N_THREADS
import time

UA = "Mozilla/5.0 (compatible; apify-actor-pdf-to-markdown/1.0; +https://apify.com)"
MAX_INLINE_MD = 1_000_000


def convert(data: bytes, max_pages: int, ocr_mode: str, table_html: bool, strip_hf: bool) -> dict:
    doc = pymupdf.open(stream=data, filetype="pdf")
    if doc.needs_pass:
        raise ValueError("PDF is password-protected")
    n = min(doc.page_count, max_pages)
    # Pages without a usable text layer are the ones that get OCR'd.
    scanned = [i for i in range(n) if len(doc[i].get_text("text").strip()) < 25 and doc[i].get_images()]
    kw: dict = {"page_chunks": True, "pages": list(range(n))}
    if ocr_mode == "off" or (ocr_mode == "auto" and not scanned):
        # No page lacks a text layer: skip OCR engine start-up (saves ~20 s on small instances).
        kw["use_ocr"] = False
    elif ocr_mode == "force":
        kw["force_ocr"] = True
    if table_html:
        kw["table_output"] = "html"
    if strip_hf:
        kw["header"] = False
        kw["footer"] = False
    res = pymupdf4llm.to_markdown(doc, **kw)
    pages = []
    for idx, p in enumerate(res):
        num = (p.get("metadata") or {}).get("page_number") or idx + 1
        md = re.sub(r"[ \t]+\n", "\n", p.get("text") or "").strip()
        pages.append({"page": num, "markdown": md, "ocr": (num - 1) in scanned or ocr_mode == "force"})
    meta = doc.metadata or {}
    return {"pageCount": doc.page_count, "pages": pages,
            "ocrPages": sum(1 for p in pages if p["ocr"]) if ocr_mode != "off" else 0,
            "title": meta.get("title") or None, "author": meta.get("author") or None,
            "subject": meta.get("subject") or None, "creationDate": meta.get("creationDate") or None,
            "toc": [{"level": l, "title": t, "page": pg} for l, t, pg in doc.get_toc()][:500]}


async def download(client: httpx.AsyncClient, url: str, max_bytes: int) -> tuple[bytes, str]:
    async with client.stream("GET", url) as r:
        r.raise_for_status()
        if int(r.headers.get("content-length") or 0) > max_bytes:
            raise ValueError(f"File larger than limit ({max_bytes // 1_000_000} MB)")
        buf = bytearray()
        async for chunk in r.aiter_bytes():
            buf.extend(chunk)
            if len(buf) > max_bytes:
                raise ValueError(f"File larger than limit ({max_bytes // 1_000_000} MB)")
        data = bytes(buf)
        if not data.lstrip()[:5].startswith(b"%PDF"):
            raise ValueError(f"Not a PDF (content-type: {r.headers.get('content-type')})")
        return data, str(r.url)


def within_limit(event: str, count: int) -> int:
    try:
        mgr = Actor.get_charging_manager()
        return min(count, int(mgr.calculate_max_event_charge_count_within_limit(event)))
    except Exception:  # noqa: BLE001 - local runs / non-PPE
        return count


async def main() -> None:
    async with Actor:
        inp = await Actor.get_input() or {}
        urls = []
        for s in inp.get("startUrls") or []:
            u = s.get("url") if isinstance(s, dict) else s
            if u and u.strip():
                urls.append(u.strip())
        if not urls:
            await Actor.fail(status_message="Provide at least one PDF URL in 'startUrls'.")
            return
        mode = inp.get("outputMode", "chunks")
        chunk_size = int(inp.get("chunkSizeChars", 2000))
        overlap = int(inp.get("chunkOverlapChars", 200))
        ocr_mode = inp.get("ocrMode", "auto")
        max_pages = int(inp.get("maxPagesPerDocument", 300))
        max_bytes = int(inp.get("maxFileSizeMb", 100)) * 1_000_000
        table_html = inp.get("tableFormat", "markdown") == "html"
        strip_hf = bool(inp.get("removeHeadersFooters", True))
        kvs = await Actor.open_key_value_store()
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        ok = failed = 0

        async with httpx.AsyncClient(timeout=120, follow_redirects=True, headers={"User-Agent": UA}) as client:
            for url in dict.fromkeys(urls):
                doc_id = hashlib.sha1(url.encode()).hexdigest()[:12]
                base = {"url": url, "docId": doc_id, "processedAt": now}
                try:
                    if within_limit("document", 1) < 1:
                        Actor.log.info("Max charge reached; stopping.")
                        break
                    data, final_url = await download(client, url, max_bytes)
                    remaining = within_limit("page", max_pages)
                    if remaining < 1:
                        break
                    _t0 = time.monotonic()
                    result = await asyncio.to_thread(convert, data, remaining, ocr_mode, table_html, strip_hf)
                    _t1 = time.monotonic()
                except Exception as e:  # noqa: BLE001
                    failed += 1
                    Actor.log.warning(f"Failed {url}: {e}")
                    await Actor.push_data({**base, "error": str(e)[:500]})
                    continue

                pages = result.pop("pages")
                full_md = "\n\n".join(p["markdown"] for p in pages)
                md_key = f"doc-{doc_id}.md"
                await kvs.set_value(md_key, full_md, content_type="text/markdown; charset=utf-8")
                try:
                    md_url = await kvs.get_public_url(md_key)
                except Exception:  # noqa: BLE001
                    md_url = None
                file_name = unquote(urlparse(final_url).path.rsplit("/", 1)[-1]) or None
                doc_info = {**base, "finalUrl": final_url, "fileName": file_name, "title": result["title"],
                            "author": result["author"], "pageCount": result["pageCount"],
                            "pagesProcessed": len(pages), "ocrPages": result["ocrPages"],
                            "sha256": hashlib.sha256(data).hexdigest(), "markdownUrl": md_url}

                if mode == "document":
                    await Actor.push_data({**doc_info, "subject": result["subject"], "creationDate": result["creationDate"],
                                           "toc": result["toc"], "wordCount": len(full_md.split()),
                                           "markdown": full_md[:MAX_INLINE_MD],
                                           "markdownTruncated": len(full_md) > MAX_INLINE_MD})
                elif mode == "pages":
                    await Actor.push_data([{**doc_info, "pageNumber": p["page"], "ocr": p["ocr"],
                                            "markdown": p["markdown"]} for p in pages])
                else:
                    chunks = chunk_pages(pages, chunk_size, overlap)
                    total = len(chunks)
                    await Actor.push_data([{**doc_info, **c, "chunkCount": total,
                                            "citation": f"{result['title'] or file_name}, p. {c['pageStart']}"
                                                        + (f"-{c['pageEnd']}" if c['pageEnd'] != c['pageStart'] else "")}
                                           for c in chunks])

                await Actor.charge("document", count=1)
                await Actor.charge("page", count=len(pages))
                if result["ocrPages"]:
                    await Actor.charge("ocr-page", count=result["ocrPages"])
                ok += 1
                Actor.log.info(f"OK {url} [{round(_t1 - _t0, 1)} s, threads={N_THREADS}]: {len(pages)} pages ({result['ocrPages']} OCR)")
        await Actor.set_status_message(f"Done: {ok} documents converted, {failed} failed")
