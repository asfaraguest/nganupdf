"""Thumbnail helper: headless (PIL) + UI (Tk PhotoImage).

Headless-safe: render_pil() hanya butuh PyMuPDF+Pillow, bisa di-test di server.
to_tk() baru import ImageTk (butuh tkinter) saat dipanggil di Windows.
"""
import io
import os

import pymupdf
from PIL import Image

THUMB_CACHE: dict = {}


def render_pil(pdf_path: str, page_no: int = 0, max_w: int = 180) -> Image.Image:
    """Render 1 halaman jadi PIL Image (RGB). page_no 0-based."""
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"File tidak ditemukan: {pdf_path}")
    with pymupdf.open(pdf_path) as doc:
        if not 0 <= page_no < doc.page_count:
            raise ValueError(f"Halaman {page_no + 1} di luar 1-{doc.page_count}")
        page = doc[page_no]
        zoom = max_w / max(1.0, page.rect.width)
        zoom = min(max(zoom, 0.1), 3.0)
        pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
        return Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")


def render_all_pil(pdf_path: str, max_w: int = 180, limit: int = 50) -> list:
    """Render beberapa halaman pertama (batasi agar hemat memori)."""
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"File tidak ditemukan: {pdf_path}")
    out = []
    with pymupdf.open(pdf_path) as doc:
        for i in range(min(doc.page_count, limit)):
            page = doc[i]
            zoom = max_w / max(1.0, page.rect.width)
            zoom = min(max(zoom, 0.1), 3.0)
            pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
            out.append(Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB"))
    return out


def to_tk(pil_img):
    """PIL -> Tk PhotoImage TANPA ImageTk (base64 PNG -> PhotoImage native).

    Disengaja: Pillow(ImageTk)<->Tk bridge sering pecah di PyInstaller
    (PyImagingPhoto invalid). PhotoImage native selalu aman frozen/portable.
    """
    import base64
    import io
    import tkinter as tk
    buf = io.BytesIO()
    pil_img.save(buf, "PNG")
    return tk.PhotoImage(data=base64.b64encode(buf.getvalue()))


def thumb_strip(parent, pdf_path: str, max_pages: int = 12, max_w: int = 120):
    """Buat strip thumbnail horizontal di frame parent. Return frame.

    Hanya dipanggil dari UI Windows (butuh tkinter). Gagal render -> label error.
    """
    import tkinter as tk
    strip = tk.Frame(parent)
    strip.pack(fill="x", pady=4)
    try:
        imgs = render_all_pil(pdf_path, max_w=max_w, limit=max_pages)
    except Exception as e:  # noqa: BLE001
        tk.Label(strip, text=f"Preview gagal: {e}").pack()
        return strip
    # tahan referensi agar tidak di-GC
    strip._refs = []  # type: ignore[attr-defined]
    for i, im in enumerate(imgs):
        try:
            ph = to_tk(im)
        except Exception:
            continue
        strip._refs.append(ph)  # type: ignore[attr-defined]
        cell = tk.Frame(strip, relief="groove", borderwidth=1)
        cell.pack(side="left", padx=3)
        tk.Label(cell, image=ph).pack()
        tk.Label(cell, text=str(i + 1), font=("Segoe UI", 8)).pack()
    with pymupdf.open(pdf_path) as doc:
        if doc.page_count > max_pages:
            tk.Label(strip, text=f"+{doc.page_count - max_pages} hal lagi...").pack(side="left", padx=6)
    return strip
