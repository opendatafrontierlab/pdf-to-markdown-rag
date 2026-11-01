> **Hosted version:** [PDF to Markdown & RAG Chunks on Apify Store](https://apify.com/opendatafrontierlab/pdf-to-markdown-rag) (pay per page, nothing to install).
>
> **This repo:** the full source of that Actor, licensed **AGPL-3.0** (see [LICENSE](LICENSE)). Built on [PyMuPDF / PyMuPDF4LLM](https://github.com/pymupdf/pymupdf4llm) (AGPL-3.0), [RapidOCR](https://github.com/RapidAI/RapidOCR) (Apache-2.0) and ONNX Runtime (MIT).
>
> Tutorial: [Turn government PDFs into RAG-ready chunks with page citations](https://github.com/opendatafrontierlab/awesome-public-data-actors/blob/main/tutorials/pdf-rag-chunks.md)

# PDF to Markdown & RAG Chunks: PDF Parser with OCR, Tables and Page Citations

**Paste PDF links and get back clean, LLM-ready Markdown**, with headings, lists and tables preserved, or **heading-aware RAG chunks with page numbers and ready-made citations** that go straight into your vector database. Scanned pages are OCR'd automatically. Everything runs inside the Actor: no OpenAI or other external AI APIs, no per-token costs, and your documents never leave Apify.

**Price:** $1.50 per 1,000 pages + $0.003 per document. Scanned pages that need OCR cost $0.004 extra. Failed or non-PDF URLs are free.

## Three output modes
| `outputMode` | You get | Best for |
|---|---|---|
| `chunks` (default) | One item per chunk with `headingPath`, `pageStart`/`pageEnd`, `approxTokens` and `citation` | RAG, vector DBs (Pinecone, Qdrant, pgvector, Weaviate), AI agents |
| `pages` | One item per page | Page-accurate citations, page-level search, QA |
| `document` | One item per PDF with full Markdown, table of contents and metadata | Summarization, archiving, fine-tuning datasets |

The full Markdown file of every document is always saved to the run's key-value store as well (`markdownUrl`).

## Why this PDF parser
- **Built for long, structured documents:** government reports, RFP/RFQ packages, Federal Register rules, standards (NIST, ISO-style), court and agency filings, manuals, annual reports and academic papers.
- **Layout-aware extraction:** it understands headings and multi-column reading order and renders tables as Markdown or HTML (`tableFormat`). Repeating page headers, footers and page numbers are removed (`removeHeadersFooters`).
- **Real citations:** every chunk carries its section path (e.g. `["Rules and Regulations", "SUPPLEMENTARY INFORMATION:"]`), its page range and a human-readable `citation` such as *"The NIST Cybersecurity Framework (CSF) 2.0, p. 8"*.
- **Built-in OCR:** `ocrMode: "auto"` OCRs only the pages that have no text layer, so you pay for OCR only when it's needed.
- **Change detection:** each document gets a SHA-256 fingerprint, so you can re-run on a schedule and re-index only the documents that changed.
- **Private and predictable:** no LLM calls, no token bills and no data sent to third parties.

## Who uses it
- **AI and RAG developers** building chatbots or agents over policies, regulations, codes, manuals or research papers.
- **Bid and proposal teams** turning 200-page solicitation PDFs into searchable sections (pairs with our [Government Bids & RFP Scraper](https://apify.com/opendatafrontierlab/us-public-bids)).
- **Compliance, policy and legal researchers** extracting rules, standards and guidance with exact page references.
- **Data teams** converting public PDF archives into Markdown for search, analytics or LLM training data.

## How to use it
1. Click **Try for free** and paste one or more public PDF URLs (`startUrls`).
2. Choose `outputMode`: `chunks` for RAG, `pages` or `document`.
3. Click **Start**. A 30-page digital PDF typically converts in seconds. Download the results as JSON, CSV or Excel, or fetch them through the API.

## Input example
```json
{ "startUrls": [{ "url": "https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf" }], "outputMode": "chunks", "chunkSizeChars": 2000, "chunkOverlapChars": 200, "ocrMode": "auto" }
```

| Field | What it does |
|---|---|
| `startUrls` | Public http(s) PDF links |
| `outputMode` | `chunks`, `pages` or `document` |
| `chunkSizeChars` / `chunkOverlapChars` | Chunk size target (~4 characters ≈ 1 token) and overlap for long sections |
| `ocrMode` | `auto` (OCR only scanned pages), `off` or `force` |
| `tableFormat` | `markdown`, or `html` for tables with merged cells |
| `maxPagesPerDocument`, `maxFileSizeMb` | Limits; skipped pages are not charged |
| `removeHeadersFooters` | Strips running headers, footers and page numbers (default on) |

## Output example (real chunk from NIST CSF 2.0, text shortened)
```json
{
  "url": "https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf",
  "docId": "8eeaabe261e4",
  "processedAt": "2026-10-29T18:39:50+00:00",
  "finalUrl": "https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf",
  "fileName": "NIST.CSWP.29.pdf",
  "title": "The NIST Cybersecurity Framework (CSF) 2.0",
  "author": "National Institute of Standards and Technology",
  "pageCount": 32,
  "pagesProcessed": 32,
  "ocrPages": 0,
  "sha256": "3c31f46fee98cac0c4323453e5109291a213b4de7fef8c058af9bf67f717433c",
  "markdownUrl": "https://api.apify.com/v2/key-value-stores/<storeId>/records/doc-8eeaabe261e4.md",
  "text": "# **2. Introduction to the CSF Core**\n\nAppendix A is the CSF Core \u2014 a set of cybersecurity outcomes arranged by Function, then Category, and finally Subcategory, as depicted in Fig. 1. These outcomes are not a checklist of actions to perform; specific actions taken to achieve an outcome will vary by organization and use case, as will the individual responsible for those actions. Additionally, the order and size of Functions, Categories, and Subcategories in the Core does not imply the sequence or importance of achieving them. The structure of the Core is intended to resonate most with those ch \u2026",
  "headingPath": [
    "2. Introduction to the CSF Core"
  ],
  "pageStart": 8,
  "pageEnd": 8,
  "chunkIndex": 13,
  "charCount": 1780,
  "approxTokens": 445,
  "chunkCount": 54,
  "citation": "The NIST Cybersecurity Framework (CSF) 2.0, p. 8"
}
```


## Pricing and cost examples (pay per event)
| Event | Price |
|---|---|
| Document converted | $0.003 |
| Page converted | $0.0015 |
| Scanned page OCR (in addition to the page price) | $0.004 |
| Actor start | $0.00005 per GB of memory |

| Scenario | Cost |
|---|---|
| 30-page digital report | ~$0.05 |
| 200-page RFP package | ~$0.30 |
| 1,000 ten-page PDFs (10,000 pages) | ~$18 |
| 10-page scanned document (all OCR) | ~$0.06 |

Failed downloads, password-protected files and non-PDF URLs are not charged. Platform compute is included in the price.

## Integrations
- **API and SDKs:** use the [Apify API](https://docs.apify.com/api/v2) or `apify-client` for Python/JavaScript. `run-sync-get-dataset-items` returns chunks in a single HTTP call.
- **LangChain and LlamaIndex:** load the results with the Apify dataset loaders and embed them directly. Each chunk's `citation` and `pageStart` fit into metadata.
- **AI agents (MCP):** connect Claude, Cursor or any MCP client through the [Apify MCP server](https://mcp.apify.com) (`opendatafrontierlab/pdf-to-markdown-rag`), so your agent can read any PDF link it finds.
- **Zapier, Make, n8n:** e.g. "new PDF link in a Google Sheet → convert → push chunks to your vector DB".

Python example:
```python
from apify_client import ApifyClient
client = ApifyClient("<YOUR_APIFY_TOKEN>")
run = client.actor("opendatafrontierlab/pdf-to-markdown-rag").call(run_input={
    "startUrls": [{"url": "https://www.govinfo.gov/content/pkg/FR-2026-10-29/pdf/2026-22093.pdf"}],
    "outputMode": "chunks"})
for chunk in client.dataset(run.default_dataset_id).iterate_items():
    print(chunk["citation"], chunk["approxTokens"], chunk["text"][:80])
```

## FAQ
**Does it work on scanned PDFs?** Yes. With `ocrMode: "auto"`, pages without a text layer are OCR'd with RapidOCR. OCR is optimized for English and Latin-script text, and quality depends on scan quality.

**Does it use GPT or another LLM?** No. Extraction and layout analysis run locally inside the Actor, so there are no token costs and nothing is sent to an AI provider.

**Can I convert private or password-protected PDFs?** Only public http(s) URLs are supported. Password-protected PDFs are reported as errors and not charged.

**How big can a PDF be?** By default up to 300 pages per document (adjustable up to 5,000) and 100 MB per file.

**Which chunk size should I use?** 1,000–2,000 characters (~250–500 tokens) works well for most embedding models. Chunks never cross a heading boundary unless a section is very short.

**Is the source code available?** Yes. It's open source under AGPL-3.0 (built on PyMuPDF / PyMuPDF4LLM); see this repository (also visible on the Actor's Source tab).

## Related Actors
- [Government Bids & RFP Scraper](https://apify.com/opendatafrontierlab/us-public-bids): find the RFPs, then convert their PDFs here.
- [Building Permits Scraper](https://apify.com/opendatafrontierlab/us-building-permits): construction leads from official permit data.

## Run it yourself
```bash
git clone https://github.com/opendatafrontierlab/pdf-to-markdown-rag.git
cd pdf-to-markdown-rag
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
npm install -g apify-cli            # Apify CLI
mkdir -p storage/key_value_stores/default
echo '{"startUrls":[{"url":"https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf"}],"outputMode":"chunks"}' \
  > storage/key_value_stores/default/INPUT.json
apify run                           # results land in ./storage/datasets/default
```
Locally, charges are only simulated (logged to a local `charging-log` dataset), so local runs cost nothing. You can also deploy it to your own Apify account with `apify push`.

**Performance tip:** if you run it in a container with a CPU limit, `src/threads.py` caps ONNX Runtime and BLAS threads to the cgroup CPU quota. Without that cap, a 6-page OCR test took 270 s instead of 20 s.

## License
AGPL-3.0. If you run a modified version as a network service, you must offer your users the modified source. PyMuPDF is also available under a commercial license from Artifex if AGPL does not fit your use.

Issues and PRs are welcome: especially PDFs that break the chunker.
