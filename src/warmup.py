import pymupdf
import pymupdf4llm

doc = pymupdf.open()
page = doc.new_page()
page.insert_text((72, 72), "Warm up OCR models", fontsize=24)
pix = page.get_pixmap(dpi=100)
scan = pymupdf.open()
p = scan.new_page()
p.insert_image(p.rect, pixmap=pix)
print(pymupdf4llm.to_markdown(scan)[:80])
