"""OCR portable via tesseract sidecar — tanpa pip tambahan, via subprocess.

Layout portable yang didukung (dicek berurutan):
  1. plugins/tesseract/tesseract(.exe)   <- build portable resmi, disarankan
  2. tesseract di PATH sistem
  3. plugins/tesseract/bin/tesseract(.exe)

tessdata dicari di: plugins/tesseract/tessdata/ lalu TESSDATA_PREFIX.
Bahasa default: ind+eng (sesuai kebutuhan Indonesia).

Strategi searchable-PDF tanpa dependensi baru:
  per halaman -> pixmap PNG (dpi~300) -> `tesseract img.pdf` (output PDF
  dengan text layer) -> gabung semua dengan PyMuPDF -> save deflate.

Semua fungsi headless-safe. Jika tesseract tidak ada -> raise OCRError
dengan pesan instalasi yang jelas untuk UI.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile

import pymupdf


class OCRError(RuntimeError):
    pass


def _root() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.abspath(os.path.join(here, "..", ".."))


def find_tesseract() -> str | None:
    cands = [
        os.path.join(_root(), "plugins", "tesseract", "tesseract.exe"),
        os.path.join(_root(), "plugins", "tesseract", "tesseract"),
        os.path.join(_root(), "plugins", "tesseract", "bin", "tesseract.exe"),
        os.path.join(_root(), "plugins", "tesseract", "bin", "tesseract"),
    ]
    for c in cands:
        if os.path.isfile(c) and os.access(c, os.X_OK | os.R_OK):
            return c
        if os.path.isfile(c):  # Windows: R_OK cukup
            return c
    return shutil.which("tesseract")


def tessdata_dir() -> str | None:
    d = os.path.join(_root(), "plugins", "tesseract", "tessdata")
    if os.path.isdir(d):
        return d
    return os.environ.get("TESSDATA_PREFIX")


def status() -> dict:
    """Dipakai UI untuk badge 'OCR siap / belum'. Headless-safe."""
    exe = find_tesseract()
    td = tessdata_dir()
    langs = []
    if td and os.path.isdir(td):
        langs = sorted(f[:-12] for f in os.listdir(td) if f.endswith(".traineddata"))
    return {"available": bool(exe), "exe": exe, "tessdata": td, "langs": langs}


def _run(exe: str, args: list[str], tessdata: str | None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    if tessdata:
        env["TESSDATA_PREFIX"] = os.path.dirname(tessdata) \
            if tessdata.endswith("tessdata") else tessdata
    return subprocess.run([exe, *args], capture_output=True, text=True,
                          timeout=300, env=env)


def ocr_image_to_text(image_path: str, lang: str = "ind+eng") -> str:
    exe = find_tesseract()
    if not exe:
        raise OCRError("Tesseract belum terpasang. Lihat plugins/ocr-README.md.")
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Gambar tidak ditemukan: {image_path}")
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "out")
        cp = _run(exe, [image_path, out, "-l", lang], tessdata_dir())
        if cp.returncode != 0:
            raise OCRError(f"Tesseract gagal: {cp.stderr.strip()[:300]}")
        with open(out + ".txt", encoding="utf-8", errors="replace") as f:
            return f.read()


def ocr_pdf_to_searchable(pdf_path: str, output: str, lang: str = "ind+eng",
                          dpi: int = 300, progress=None) -> str:
    """PDF scan -> PDF searchable (text layer). progress(i, total) opsional."""
    try:
        from src.core import pdf_ops  # via app (root di path)
    except ImportError:
        from core import pdf_ops  # via tests (src/ di path)

    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"File tidak ditemukan: {pdf_path}")
    exe = find_tesseract()
    if not exe:
        raise OCRError("Tesseract belum terpasang. Lihat plugins/ocr-README.md.")
    if not 100 <= dpi <= 600:
        raise ValueError("DPI 100-600.")
    parent = os.path.dirname(os.path.abspath(output))
    if parent:
        os.makedirs(parent, exist_ok=True)

    with pymupdf.open(pdf_path) as doc:
        total = doc.page_count
        if total == 0:
            raise ValueError("PDF kosong.")
        with tempfile.TemporaryDirectory() as td:
            pdf_parts = []
            zoom = dpi / 72.0
            for i, page in enumerate(doc):
                if progress:
                    progress(i, total)
                pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
                img_fp = os.path.join(td, f"p{i:04d}.png")
                pix.save(img_fp)
                base = os.path.join(td, f"o{i:04d}")
                cp = _run(exe, [img_fp, base, "-l", lang, "pdf"], tessdata_dir())
                if cp.returncode != 0:
                    raise OCRError(f"Hal {i + 1} gagal: {cp.stderr.strip()[:300]}")
                pdf_parts.append(base + ".pdf")
            if progress:
                progress(total, total)
            # gabung via core agar konsisten (garbage+deflate)
            pdf_ops.merge_pdfs(pdf_parts, output)
    return output
