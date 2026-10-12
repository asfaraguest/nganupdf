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

    og = os.path.join(TMP, "org.pdf")
    # balik urutan 5 hal gab.pdf + putar hal pertama 90 + tambah 1 hal dari a.pdf
    items = [(0, 4, 90), (0, 3, 0), (0, 2, 0), (1, 0, 0)]
    pdf_ops.organize_pdfs(m, og, items, extras=[a])
    assert pdf_ops.pdf_info(og)["pages"] == 4
    print("organize OK")

    r = pdf_ops.repair_pdf(m, os.path.join(TMP, "rep.pdf"))
    assert r["pages"] == 5
    print(f"repair OK {r['before']} -> {r['after']}")

    cr = os.path.join(TMP, "crop.pdf")
    pdf_ops.crop_pdf(a, cr, "*", m_left=10, m_top=10, m_right=10, m_bottom=10)
    print("crop OK")

    rd = os.path.join(TMP, "red.pdf")
    rr = pdf_ops.redact_text(a, rd, "DokA")
    assert rr["hits"] >= 2
    print(f"redact OK {rr['hits']} hit")

    tx = os.path.join(TMP, "txt.pdf")
    pdf_ops.add_text(a, tx, "CAP", "*", pos="tengah", fontsize=20, color="merah")
    print("add_text OK")

    sg = os.path.join(TMP, "sig.pdf")
    pdf_ops.sign_pdf(a, sg, img, "*", pos="kanan-bawah", scale=20)
    print("sign OK")

    with open(os.path.join(TMP, "t.html"), "w", encoding="utf-8") as f:
        f.write("<h1>Halo</h1><p>Tes html.</p>")
    hp = os.path.join(TMP, "dari-html.pdf")
    pdf_ops.html_to_pdf(os.path.join(TMP, "t.html"), hp)
    assert "Halo" in pymupdf.open(hp)[0].get_text()
    print("html2pdf OK")

    md = os.path.join(TMP, "hasil.md")
    pdf_ops.pdf_to_markdown(a, md)
    assert "# Halaman 1" in open(md, encoding="utf-8").read()
    print("pdf2md OK")

    print("\nSEMUA TEST LOLOS")


if __name__ == "__main__":
    main()
