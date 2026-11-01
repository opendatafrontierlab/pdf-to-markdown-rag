# Changelog

## 1.0 (build 1.0.7), 2026-10-29
- Fixed: `headingPath` nesting. A heading now closes every open heading of the same or a deeper level, so sibling sections (e.g. two `##` headings with no `#` above them) no longer nest under each other. Previously `## A` then `## B` gave `["A", "B"]`; now it gives `["B"]`.
- No change to pricing, input or output fields.

## 1.0 (builds 1.0.1-1.0.6)
- Initial public release: PDF URLs to Markdown, pages or heading-aware RAG chunks with page citations; automatic OCR for scanned pages.
