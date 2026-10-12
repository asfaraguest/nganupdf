"""Smoke test headless untuk core (tanpa tkinter): buat PDF dummy lalu
merge/split/rotate/compress/img2pdf/pdf2img/protect/unlock."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from PIL import Image
import pymupdf

from core import pdf_ops

TMP = os.path.join(os.path.dirname(__file__), "tmp")
os.makedirs(TMP, exist_ok=True)


def make_pdf(path, text, pages=1):
    d = pymupdf.open()
    for i in range(pages):
        p = d.new_page()
        p.insert_text((72, 72), f"{text} hal {i + 1}")
    d.save(path)
    d.close()


def main():
    a = os.path.join(TMP, "a.pdf")
    b = os.path.join(TMP, "b.pdf")
    make_pdf(a, "DokA", 2)
    make_pdf(b, "DokB", 3)
    print("info a:", pdf_ops.pdf_info(a))

    m = os.path.join(TMP, "gab.pdf")
    pdf_ops.merge_pdfs([a, b], m)
    assert pdf_ops.pdf_info(m)["pages"] == 5, "merge gagal"
    print("merge OK -> 5 hal")

    outs = pdf_ops.split_pdf(m, TMP, "per-halaman", prefix="s")
    assert len(outs) == 5, "split gagal"
    print("split OK -> 5 file")

    ex = os.path.join(TMP, "ex.pdf")
    pdf_ops.extract_pages(m, ex, "1-2")
    assert pdf_ops.pdf_info(ex)["pages"] == 2
    print("extract OK")

    dl = os.path.join(TMP, "del.pdf")
    pdf_ops.delete_pages(m, dl, "1")
    assert pdf_ops.pdf_info(dl)["pages"] == 4
    print("delete OK")

    ro = os.path.join(TMP, "rot.pdf")
    pdf_ops.rotate_pdf(a, ro, 90)
    print("rotate OK")

    img = os.path.join(TMP, "g.png")
    Image.new("RGB", (400, 300), (200, 30, 30)).save(img)
    ip = os.path.join(TMP, "dari-gambar.pdf")
    pdf_ops.images_to_pdf([img, img], ip)
    print("img2pdf OK")

    ims = pdf_ops.pdf_to_images(a, TMP, dpi=72, fmt="png")
    assert len(ims) == 2
    print("pdf2img OK")

    c = os.path.join(TMP, "kecil.pdf")
    r = pdf_ops.compress_pdf(m, c, image_quality=50, scale=0.8)
    print(f"compress OK {r['before']} -> {r['after']} ({r['ratio']}%)")

    wm = os.path.join(TMP, "wm.pdf")
    pdf_ops.add_watermark(a, wm, "DRAF")
    pdf_ops.add_page_numbers(a, os.path.join(TMP, "num.pdf"))
    pdf_ops.set_metadata(a, os.path.join(TMP, "meta.pdf"), {"title": "Tes"})
    print("watermark/number/metadata OK")

    pr = os.path.join(TMP, "locked.pdf")
    pdf_ops.protect_pdf(a, pr, "1234")
    assert pdf_ops.pdf_info(pr)["encrypted"]
    ul = os.path.join(TMP, "unlocked.pdf")
    pdf_ops.unlock_pdf(pr, ul, "1234")
    print("protect/unlock OK")

    print("\nSEMUA TEST LOLOS")


if __name__ == "__main__":
    main()
