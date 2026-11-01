"""Heading-aware Markdown chunking with page citations."""
from __future__ import annotations

import re

HEADING = re.compile(r"^(#{1,6})\s+\**(.+?)\**\s*$")


def _split_long(text: str, max_chars: int, overlap: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    parts, start = [], 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        if end < len(text):
            cut = max(text.rfind("\n\n", start, end), text.rfind(". ", start, end))
            if cut > start + max_chars // 2:
                end = cut + 1
        parts.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return [p for p in parts if p]


def chunk_pages(pages: list[dict], max_chars: int = 2000, overlap: int = 200) -> list[dict]:
    """pages: [{'page': n, 'markdown': str}] -> chunks with headingPath and pageStart/pageEnd."""
    blocks: list[tuple[int, list[str], str]] = []  # (page, headingPath, paragraph)
    stack: list[tuple[int, str]] = []  # (level, title) of open headings
    path: list[str] = []
    for pg in pages:
        for para in re.split(r"\n\s*\n", pg["markdown"]):
            para = para.strip()
            if not para:
                continue
            m = HEADING.match(para.splitlines()[0])
            if m:
                level = len(m.group(1))
                while stack and stack[-1][0] >= level:
                    stack.pop()
                stack.append((level, m.group(2).strip()))
                path = [h for _, h in stack]
            blocks.append((pg["page"], list(path), para))

    chunks: list[dict] = []
    buf: list[tuple[int, str]] = []
    buf_path: list[str] = []

    def flush():
        if not buf:
            return
        text = "\n\n".join(t for _, t in buf)
        pages_ = [p for p, _ in buf]
        for piece in _split_long(text, max_chars, overlap):
            chunks.append({"text": piece, "headingPath": buf_path, "pageStart": min(pages_), "pageEnd": max(pages_)})
        buf.clear()

    for page, hpath, para in blocks:
        is_heading = bool(HEADING.match(para.splitlines()[0]))
        size = sum(len(t) for _, t in buf)
        if buf and (is_heading and size > min(300, max_chars // 4) or size + len(para) > max_chars):
            flush()
        if not buf:
            buf_path = hpath
        buf.append((page, para))
    flush()
    for i, c in enumerate(chunks):
        c["chunkIndex"] = i
        c["charCount"] = len(c["text"])
        c["approxTokens"] = round(len(c["text"]) / 4)
    return chunks
