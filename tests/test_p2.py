"""Test P2 headless: thumbnails (PIL) + OCR status/skip.

- Thumbnail: buat PDF dummy, render 2 halaman, assert ukuran > 0.
- OCR: jika tesseract tidak ada -> status()['available'] False dan
  ocr_pdf_to_searchable raise OCRError (bukan crash lain).
  Jika ada -> OCR 1 halaman dan assert file keluar.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pymupdf

from core import ocr_ops
from ui import thumbs

TMP = os.path.join(os.path.dirname(__file__), "tmp")
os.makedirs(TMP, exist_ok=True)


def main():
    # --- thumbnails ---
    pdf = os.path.join(TMP, "thumb.pdf")
    d = pymupdf.open()
    for i in range(2):
        d.new_page().insert_text((72, 72), f"Halo hal {i + 1}")
    d.save(pdf)
    d.close()

    im = thumbs.render_pil(pdf, 0, max_w=120)
    assert im.size[0] > 0 and im.size[1] > 0, "thumbnail kosong"
    print(f"thumb 1 hal OK: {im.size}")
    all_im = thumbs.render_all_pil(pdf, max_w=120)
    assert len(all_im) == 2, "render_all gagal"
    print("thumb semua hal OK")

    # --- OCR status ---
    st = ocr_ops.status()
    print(f"tesseract: available={st['available']} exe={st['exe']} langs={st['langs']}")
    if not st["available"]:
        try:
            ocr_ops.ocr_pdf_to_searchable(pdf, os.path.join(TMP, "ocr.pdf"))
            raise SystemExit("seharusnya OCRError saat tesseract absen")
        except ocr_ops.OCRError as e:
            print(f"OCR absen ditangani OK: {e}")
    else:
        out = os.path.join(TMP, "ocr.pdf")
        ocr_ops.ocr_pdf_to_searchable(pdf, out, lang="eng", dpi=200)
        assert os.path.isfile(out) and os.path.getsize(out) > 0
        print(f"OCR jalan OK -> {out}")

    print("\nTEST P2 LOLOS")


if __name__ == "__main__":
    main()
