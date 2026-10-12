"""Core PDF operations — pure PyMuPDF + Pillow, no GUI, no tkinter.

Semua fungsi: input path -> output path, raise ValueError/FileNotFoundError
dengan pesan Indonesia yang ramah UI. Aman dipanggil dari thread worker.
Portable: hanya pakai path relatif/absolut, tanpa registry.
"""

from __future__ import annotations

import io
import os
import re

import pymupdf  # PyMuPDF (MuPDF)
from PIL import Image

SUPPORTED_IMG_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff")


# ---------------------------------------------------------------- helpers
def _require_exists(path: str) -> str:
    if not path or not os.path.isfile(path):
        raise FileNotFoundError(f"File tidak ditemukan: {path}")
    return path


def _ensure_parent(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def parse_page_spec(spec: str, page_count: int) -> list[int]:
    """'1-3,5' (1-based) -> [0,1,2,4]. '*' / kosong -> semua halaman."""
    if not spec or spec.strip() in ("*", "semua", "all"):
        return list(range(page_count))
    out: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        m = re.fullmatch(r"(\d+)\s*-\s*(\d+)", part)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            if a < 1 or b < 1 or a > page_count or b > page_count:
                raise ValueError(f"Rentang halaman di luar 1-{page_count}: {part}")
            lo, hi = (a, b) if a <= b else (b, a)
            out.extend(range(lo - 1, hi))
        elif re.fullmatch(r"\d+", part):
            n = int(part)
            if n < 1 or n > page_count:
                raise ValueError(f"Halaman di luar 1-{page_count}: {part}")
            out.append(n - 1)
        else:
            raise ValueError(f"Format halaman salah: '{part}' (contoh: 1-3,5)")
    # dedup sambil jaga urutan
    seen, res = set(), []
    for i in out:
        if i not in seen:
            seen.add(i)
            res.append(i)
    return res


def pdf_info(path: str) -> dict:
    _require_exists(path)
    with pymupdf.open(path) as doc:
        return {
            "pages": doc.page_count,
            "metadata": dict(doc.metadata or {}),
            "encrypted": doc.is_encrypted,
            "size_bytes": os.path.getsize(path),
        }


# ---------------------------------------------------------------- P0: merge
def merge_pdfs(inputs: list[str], output: str) -> str:
    if not inputs:
        raise ValueError("Belum ada file untuk digabung.")
    if len(inputs) < 2:
        raise ValueError("Pilih minimal 2 file PDF untuk digabung.")
    for p in inputs:
        _require_exists(p)
        if not p.lower().endswith(".pdf"):
            raise ValueError(f"Bukan PDF: {p}")
    _ensure_parent(output)
    out = pymupdf.open()
    try:
        for p in inputs:
            with pymupdf.open(p) as src:
                if src.is_encrypted:
                    raise ValueError(f"PDF terkunci, buka dulu: {p}")
                out.insert_pdf(src)
        out.save(output, garbage=4, deflate=True)
    finally:
        out.close()
    return output


# ---------------------------------------------------------------- P0: split / extract / delete
def split_pdf(path: str, out_dir: str, spec: str = "", prefix: str = "halaman") -> list[str]:
    """Pecah per halaman (spec kosong) atau per rentang ('1-3,4-5')."""
    _require_exists(path)
    os.makedirs(out_dir, exist_ok=True)
    made: list[str] = []
    with pymupdf.open(path) as doc:
        if doc.is_encrypted:
            raise ValueError("PDF terkunci — gunakan menu Unlock dulu.")
        if not spec or spec.strip() in ("*", "semua", "all", "per-halaman"):
            for i in range(doc.page_count):
                nd = pymupdf.open()
                nd.insert_pdf(doc, from_page=i, to_page=i)
                fp = os.path.join(out_dir, f"{prefix}-{i + 1:03d}.pdf")
                nd.save(fp, garbage=4, deflate=True)
                nd.close()
                made.append(fp)
        else:
            groups = [g.strip() for g in spec.split(";") if g.strip()]
            if not groups:  # koma saja -> satu file berisi halaman pilihan
                pages = parse_page_spec(spec, doc.page_count)
                nd = pymupdf.open()
                for pno in pages:
                    nd.insert_pdf(doc, from_page=pno, to_page=pno)
                fp = os.path.join(out_dir, f"{prefix}-pilihan.pdf")
                nd.save(fp, garbage=4, deflate=True)
                nd.close()
                made.append(fp)
            else:  # '1-3;4-5' -> dua file
                for k, g in enumerate(groups, 1):
                    pages = parse_page_spec(g, doc.page_count)
                    nd = pymupdf.open()
                    for pno in pages:
                        nd.insert_pdf(doc, from_page=pno, to_page=pno)
                    fp = os.path.join(out_dir, f"{prefix}-bagian{k}.pdf")
                    nd.save(fp, garbage=4, deflate=True)
                    nd.close()
                    made.append(fp)
    return made


def extract_pages(path: str, output: str, spec: str) -> str:
    _require_exists(path)
    _ensure_parent(output)
    with pymupdf.open(path) as doc:
        pages = parse_page_spec(spec, doc.page_count)
        if not pages:
            raise ValueError("Pilih minimal 1 halaman.")
        nd = pymupdf.open()
        for pno in pages:
            nd.insert_pdf(doc, from_page=pno, to_page=pno)
        nd.save(output, garbage=4, deflate=True)
        nd.close()
    return output


def delete_pages(path: str, output: str, spec: str) -> str:
    _require_exists(path)
    _ensure_parent(output)
    with pymupdf.open(path) as doc:
        drop = set(parse_page_spec(spec, doc.page_count))
        keep = [i for i in range(doc.page_count) if i not in drop]
        if not keep:
            raise ValueError("Tidak boleh menghapus semua halaman.")
        nd = pymupdf.open()
        for pno in keep:
            nd.insert_pdf(doc, from_page=pno, to_page=pno)
        nd.save(output, garbage=4, deflate=True)
        nd.close()
    return output


# ---------------------------------------------------------------- P0: rotate
def rotate_pdf(path: str, output: str, angle: int, spec: str = "") -> str:
    if angle % 90 != 0:
        raise ValueError("Sudut harus kelipatan 90 (90/180/270).")
    _require_exists(path)
    _ensure_parent(output)
    with pymupdf.open(path) as doc:
        pages = parse_page_spec(spec, doc.page_count)
        for pno in pages:
            page = doc[pno]
            page.set_rotation((page.rotation + angle) % 360)
        doc.save(output, garbage=4, deflate=True)
    return output


# ---------------------------------------------------------------- P0: compress
def compress_pdf(path: str, output: str, image_quality: int = 60,
                 scale: float = 1.0, dpi_fallback: int = 150) -> dict:
    """Compress tanpa tool eksternal: downscale + recompress JPEG + deflate.

    quality 1-95, scale 0.3-1.0. Return dict {output, before, after, ratio}.
    """
    _require_exists(path)
    if not 1 <= image_quality <= 95:
        raise ValueError("Kualitas harus 1-95.")
    if not 0.2 <= scale <= 1.0:
        raise ValueError("Skala harus 0.2-1.0.")
    _ensure_parent(output)
    before = os.path.getsize(path)
    with pymupdf.open(path) as doc:
        if doc.is_encrypted:
            raise ValueError("PDF terkunci — unlock dulu.")
        for page in doc:
            for img in page.get_images(full=True):
                xref = img[0]
                try:
                    pix = pymupdf.Pixmap(doc, xref)
                    if pix.n > 4:  # CMYK -> RGB
                        pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
                    mode = "RGBA" if pix.alpha else "RGB"
                    im = Image.frombytes(mode, (pix.width, pix.height), pix.samples)
                    if im.mode == "RGBA":
                        bg = Image.new("RGB", im.size, (255, 255, 255))
                        bg.paste(im, mask=im.split()[3])
                        im = bg
                    w, h = im.size
                    if scale < 1.0:
                        im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))),
                                       Image.LANCZOS)
                    buf = io.BytesIO()
                    im.save(buf, "JPEG", quality=image_quality, optimize=True,
                            progressive=True)
                    doc.update_stream(xref, buf.getvalue())
                except Exception:
                    continue  # gambar mask/aneh -> lewati, jangan gagal total
        doc.save(output, garbage=4, deflate=True, clean=True)
    after = os.path.getsize(output)
    return {"output": output, "before": before, "after": after,
            "ratio": round(100 * (1 - after / before), 1) if before else 0.0}


# ---------------------------------------------------------------- P0: images <-> pdf
def images_to_pdf(images: list[str], output: str, fit_a4: bool = True) -> str:
    if not images:
        raise ValueError("Belum ada gambar.")
    _ensure_parent(output)
    doc = pymupdf.open()
    try:
        for p in images:
            _require_exists(p)
            if not p.lower().endswith(SUPPORTED_IMG_EXTS):
                raise ValueError(f"Bukan gambar: {p}")
            im = Image.open(p)
            if im.mode in ("RGBA", "LA", "P"):
                bg = Image.new("RGB", im.convert("RGBA").size, (255, 255, 255))
                bg.paste(im.convert("RGBA"), mask=im.convert("RGBA").split()[3]
                         if im.convert("RGBA").mode == "RGBA" else None)
                im = bg
            else:
                im = im.convert("RGB")
            buf = io.BytesIO()
            im.save(buf, "JPEG", quality=90)
            w, h = im.size
            if fit_a4:
                # A4 portrait 595x842 pt; fit gambar proporsional di tengah
                pw, ph = 595.0, 842.0
                s = min(pw / w, ph / h)
                iw, ih = w * s, h * s
                page = doc.new_page(width=pw, height=ph)
                page.insert_image(pymupdf.Rect((pw - iw) / 2, (ph - ih) / 2,
                                               (pw + iw) / 2, (ph + ih) / 2),
                                  stream=buf.getvalue())
            else:
                page = doc.new_page(width=w * 72 / 150, height=h * 72 / 150)
                page.insert_image(page.rect, stream=buf.getvalue())
        doc.save(output, garbage=4, deflate=True)
    finally:
        doc.close()
    return output


def pdf_to_images(path: str, out_dir: str, dpi: int = 150, fmt: str = "png") -> list[str]:
    _require_exists(path)
    if fmt not in ("png", "jpg"):
        raise ValueError("Format harus png/jpg.")
    if not 36 <= dpi <= 300:
        raise ValueError("DPI 36-300.")
    os.makedirs(out_dir, exist_ok=True)
    made: list[str] = []
    with pymupdf.open(path) as doc:
        zoom = dpi / 72.0
        for i, page in enumerate(doc):
            pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
            fp = os.path.join(out_dir, f"halaman-{i + 1:03d}.{fmt}")
            if fmt == "png":
                pix.save(fp)
            else:
                im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                im.save(fp, "JPEG", quality=90)
            made.append(fp)
    return made


def page_thumbnail(path: str, page_no: int, max_w: int = 180) -> bytes:
    """PNG kecil untuk preview UI. page_no 0-based."""
    _require_exists(path)
    with pymupdf.open(path) as doc:
        page = doc[page_no]
        zoom = max_w / max(1, page.rect.width)
        pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
        return pix.tobytes("png")


# ---------------------------------------------------------------- P2: organize
def organize_pdfs(primary: str, output: str, items: list[tuple[int, int, int]],
                  extras: list[str] | None = None) -> str:
    """Susun ulang halaman ala iLovePDF Organize, tanpa render ulang.

    items = [(src, orig_idx_0based, extra_rot90), ...] urutan baru.
    src 0 = primary, 1..n = extras. extra_rot kelipatan 90 (ditambah ke
    rotasi asli). Entri yang tidak ada di items = dihapus.
    """
    _require_exists(primary)
    extras = list(extras or [])
    for p in extras:
        _require_exists(p)
    if not items:
        raise ValueError("Tidak ada halaman tersisa (semua dihapus?).")
    _ensure_parent(output)
    docs = [pymupdf.open(primary)] + [pymupdf.open(p) for p in extras]
    try:
        for d in docs:
            if d.is_encrypted:
                raise ValueError("Ada PDF terkunci — unlock dulu.")
        nd = pymupdf.open()
        for (src, orig, rot) in items:
            if not 0 <= src < len(docs):
                raise ValueError(f"Sumber halaman salah: {src}")
            doc = docs[src]
            if not 0 <= orig < doc.page_count:
                raise ValueError(f"Halaman {orig + 1} di luar jangkauan.")
            if rot % 90 != 0:
                raise ValueError("Rotasi harus kelipatan 90.")
            nd.insert_pdf(doc, from_page=orig, to_page=orig)
            if rot:
                pg = nd[-1]
                pg.set_rotation((doc[orig].rotation + rot) % 360)
        nd.save(output, garbage=4, deflate=True)
        nd.close()
    finally:
        for d in docs:
            d.close()
    return output


# ---------------------------------------------------------------- P3: repair
def repair_pdf(path: str, output: str) -> dict:
    """Buka + simpan ulang (garbage+clean+deflate). MuPDF otomatis
    memperbaiki struktur rusak saat open; gagal total -> error jelas."""
    _require_exists(path)
    _ensure_parent(output)
    before = os.path.getsize(path)
    try:
        doc = pymupdf.open(path)
    except Exception as e:
        raise ValueError(f"PDF tidak bisa dibuka (rusak berat?): {e}")
    try:
        if doc.is_encrypted:
            raise ValueError("PDF terkunci — unlock dulu.")
        doc.save(output, garbage=4, clean=True, deflate=True)
        pages = doc.page_count
    finally:
        doc.close()
    after = os.path.getsize(output)
    return {"output": output, "before": before, "after": after, "pages": pages}


# ---------------------------------------------------------------- P3: crop / redact / sign / text
def crop_pdf(path: str, output: str, spec: str = "",
             m_left: int = 5, m_top: int = 5, m_right: int = 5, m_bottom: int = 5) -> str:
    """Potong tepi halaman (cropbox). Margin dalam persen 0-40 per sisi."""
    for v in (m_left, m_top, m_right, m_bottom):
        if not 0 <= int(v) <= 40:
            raise ValueError("Margin harus 0-40%.")
    _require_exists(path)
    _ensure_parent(output)
    with pymupdf.open(path) as doc:
        if doc.is_encrypted:
            raise ValueError("PDF terkunci — unlock dulu.")
        pages = parse_page_spec(spec, doc.page_count)
        for pno in pages:
            page = doc[pno]
            r = page.rect
            page.set_cropbox(pymupdf.Rect(
                r.x0 + r.width * int(m_left) / 100,
                r.y0 + r.height * int(m_top) / 100,
                r.x1 - r.width * int(m_right) / 100,
                r.y1 - r.height * int(m_bottom) / 100))
        doc.save(output, garbage=4, deflate=True)
    return output


def redact_text(path: str, output: str, queries: str = "") -> dict:
    """Hitamkan permanen semua kemunculan kata (koma-pisah, case-insensitive)."""
    words = [w.strip() for w in (queries or "").replace("\n", ",").split(",") if w.strip()]
    if not words:
        raise ValueError("Isi dulu kata yang mau dihitamkan.")
    _require_exists(path)
    _ensure_parent(output)
    count = 0
    with pymupdf.open(path) as doc:
        if doc.is_encrypted:
            raise ValueError("PDF terkunci — unlock dulu.")
        for page in doc:
            for w in words:
                for inst in page.search_for(w):
                    page.add_redact_annot(inst, fill=(0, 0, 0))
                    count += 1
            page.apply_redactions()
        doc.save(output, garbage=4, deflate=True)
    if not count:
        raise ValueError("Kata tidak ditemukan di PDF.")
    return {"output": output, "hits": count}


POS9 = {  # fraksi (x, y) dari rect halaman
    "kiri-atas": (0.08, 0.10), "tengah-atas": (0.50, 0.10), "kanan-atas": (0.92, 0.10),
    "kiri-tengah": (0.08, 0.50), "tengah": (0.50, 0.50), "kanan-tengah": (0.92, 0.50),
    "kiri-bawah": (0.08, 0.90), "tengah-bawah": (0.50, 0.90), "kanan-bawah": (0.92, 0.90),
}

COLORS = {"hitam": (0, 0, 0), "merah": (0.8, 0, 0), "biru": (0, 0, 0.8),
          "hijau": (0, 0.5, 0), "abu": (0.4, 0.4, 0.4)}


def _pos_point(rect, pos: str):
    fx, fy = POS9.get(pos, POS9["kanan-bawah"])
    return rect.x0 + rect.width * fx, rect.y0 + rect.height * fy


def add_text(path: str, output: str, text: str = "", spec: str = "",
             pos: str = "kanan-bawah", fontsize: int = 12,
             color: str = "hitam") -> str:
    if not (text or "").strip():
        raise ValueError("Teks kosong.")
    if not 6 <= int(fontsize) <= 72:
        raise ValueError("Ukuran font 6-72.")
    _require_exists(path)
    _ensure_parent(output)
    col = COLORS.get(color, COLORS["hitam"])
    with pymupdf.open(path) as doc:
        if doc.is_encrypted:
            raise ValueError("PDF terkunci — unlock dulu.")
        for pno in parse_page_spec(spec, doc.page_count):
            page = doc[pno]
            x, y = _pos_point(page.rect, pos)
            page.insert_text((x - len(text) * int(fontsize) * 0.28, y),
                             text, fontsize=int(fontsize), color=col, overlay=True)
        doc.save(output, garbage=4, deflate=True)
    return output


def sign_pdf(path: str, output: str, img_path: str, spec: str = "",
             pos: str = "kanan-bawah", scale: int = 25) -> str:
    """Tempel gambar tanda tangan. scale = % lebar halaman."""
    _require_exists(path)
    _require_exists(img_path)
    if not img_path.lower().endswith(SUPPORTED_IMG_EXTS):
        raise ValueError("File tanda tangan harus gambar (png/jpg).")
    if not 5 <= int(scale) <= 80:
        raise ValueError("Skala 5-80%.")
    _ensure_parent(output)
    im = Image.open(img_path).convert("RGBA")
    buf = __import__("io").BytesIO()
    im.save(buf, "PNG")
    blob = buf.getvalue()
    iw, ih = im.size
    with pymupdf.open(path) as doc:
        if doc.is_encrypted:
            raise ValueError("PDF terkunci — unlock dulu.")
        for pno in parse_page_spec(spec, doc.page_count):
            page = doc[pno]
            r = page.rect
            w = r.width * int(scale) / 100
            h = w * ih / iw
            cx, cy = _pos_point(r, pos)
            page.insert_image(pymupdf.Rect(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2),
                              stream=blob, overlay=True)
        doc.save(output, garbage=4, deflate=True)
    return output


# ---------------------------------------------------------------- P3: html -> pdf, pdf -> markdown
def html_to_pdf(html_path: str, output: str) -> str:
    if not (html_path or "").lower().endswith((".html", ".htm")):
        raise ValueError("Pilih file .html/.htm.")
    _require_exists(html_path)
    _ensure_parent(output)
    with open(html_path, encoding="utf-8", errors="replace") as f:
        html = f.read()
    if not html.strip():
        raise ValueError("File HTML kosong.")

    def rectfn(_pno, _filled):
        mb = pymupdf.Rect(0, 0, 595, 842)  # A4 portrait 72dpi
        return mb, mb + (36, 36, -36, -36), pymupdf.Matrix(1, 1)

    story = pymupdf.Story(html=html, em=12)
    w = pymupdf.DocumentWriter(output)
    try:
        story.write(w, rectfn)
    finally:
        w.close()
    return output


def pdf_to_markdown(path: str, output: str) -> str:
    _require_exists(path)
    _ensure_parent(output)
    with pymupdf.open(path) as doc:
        if doc.is_encrypted:
            raise ValueError("PDF terkunci — unlock dulu.")
        if doc.page_count == 0:
            raise ValueError("PDF kosong.")
        parts = []
        for i, page in enumerate(doc):
            txt = page.get_text().strip()
            parts.append(f"# Halaman {i + 1}\n\n{txt if txt else '*(kosong / hasil scan)*'}\n")
    with open(output, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    return output


# ---------------------------------------------------------------- P1: watermark / pagenum / metadata / security
def add_watermark(path: str, output: str, text: str, fontsize: int = 48,
                  rotate: int = 0, opacity: float = 0.15) -> str:
    if not text.strip():
        raise ValueError("Teks watermark kosong.")
    if rotate % 90 != 0:
        rotate = 0  # PyMuPDF insert_text hanya dukung 0/90/180/270
    _require_exists(path)
    _ensure_parent(output)
    with pymupdf.open(path) as doc:
        for page in doc:
            r = page.rect
            cx, cy = r.width / 2 - len(text) * fontsize * 0.25, r.height / 2
            page.insert_text(
                (cx, cy),
                text, fontsize=fontsize, rotate=rotate,
                color=(0.7, 0.7, 0.7), overlay=True)
            # opacity via annot workaround tidak stabil lintas viewer;
            # warna abu + overlay sudah cukup terbaca ringan.
        doc.save(output, garbage=4, deflate=True)
    return output


def add_page_numbers(path: str, output: str, pos: str = "bawah-tengah",
                      fontsize: int = 10, template: str = "{n} / {total}") -> str:
    _require_exists(path)
    _ensure_parent(output)
    with pymupdf.open(path) as doc:
        total = doc.page_count
        for i, page in enumerate(doc):
            label = template.format(n=i + 1, total=total)
            r = page.rect
            tw = len(label) * fontsize * 0.55
            y = r.height - 30
            x = {"bawah-kiri": 30, "bawah-tengah": (r.width - tw) / 2,
                 "bawah-kanan": r.width - tw - 30}.get(pos, (r.width - tw) / 2)
            page.insert_text((x, y), label, fontsize=fontsize, color=(0.3, 0.3, 0.3))
        doc.save(output, garbage=4, deflate=True)
    return output


def get_metadata(path: str) -> dict:
    _require_exists(path)
    with pymupdf.open(path) as doc:
        return dict(doc.metadata or {})


def set_metadata(path: str, output: str, meta: dict) -> str:
    _require_exists(path)
    _ensure_parent(output)
    allow = {"title", "author", "subject", "keywords", "creator", "producer"}
    clean = {k: str(v) for k, v in (meta or {}).items() if k in allow}
    with pymupdf.open(path) as doc:
        doc.set_metadata(clean)
        doc.save(output, garbage=4, deflate=True)
    return output


def protect_pdf(path: str, output: str, user_pw: str, owner_pw: str = "") -> str:
    if not user_pw:
        raise ValueError("Password user kosong.")
    _require_exists(path)
    _ensure_parent(output)
    with pymupdf.open(path) as doc:
        doc.save(output, garbage=4, deflate=True,
                 encryption=pymupdf.PDF_ENCRYPT_AES_256,
                 user_pw=user_pw, owner_pw=owner_pw or user_pw)
    return output


def unlock_pdf(path: str, output: str, password: str) -> str:
    _require_exists(path)
    _ensure_parent(output)
    with pymupdf.open(path) as doc:
        if doc.is_encrypted:
            if not doc.authenticate(password):
                raise ValueError("Password salah.")
        doc.save(output, garbage=4, deflate=True)
    return output
