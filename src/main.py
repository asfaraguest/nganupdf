"""PDFTool Portable — dashboard grid ala PDF24 (tkinter + ttkbootstrap)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from src.core import ocr_ops, pdf_ops, recent, settings  # noqa: E402

TOOLS = [
    ("⧉", "Merge", "Gabung PDF", "primary"),
    ("✂", "Split", "Pecah + preview", "success"),
    ("⟳", "Rotate", "Putar halaman", "info"),
    ("🗑", "Hapus/Extract", "Hapus atau ambil halaman", "warning"),
    ("🗜", "Compress", "Kecilkan ukuran", "danger"),
    ("🖼", "Img→PDF", "Gambar jadi PDF", "primary"),
    ("📄", "PDF→Img", "PDF jadi gambar", "secondary"),
    ("©", "Watermark", "Tanda air teks", "dark"),
    ("#", "Nomor", "Nomor halaman", "light"),
    ("🏷", "Metadata", "Judul/penulis", "info"),
    ("🔒", "Protect", "Kunci password", "warning"),
    ("🔓", "Unlock", "Buka kunci", "success"),
    ("👁", "OCR", "Scan jadi teks", "info"),
]


def _ask_out(default_name="hasil.pdf"):
    from tkinter import filedialog
    s = settings.load()
    return filedialog.asksaveasfilename(
        initialdir=s.get("last_dir") or os.path.expanduser("~"),
        initialfile=default_name, defaultextension=".pdf",
        filetypes=[("PDF", "*.pdf")]) or ""


def _remember(path):
    if path:
        s = settings.load()
        s["last_dir"] = os.path.dirname(path)
        settings.save(s)


_recent_lb = None  # diisi dashboard, dipakai refresh_recent()


def refresh_recent():
    """Isi ulang listbox recent (aman dipanggil dari thread via after)."""
    if _recent_lb is None:
        return
    try:
        lb = _recent_lb
        lb.delete(0, "end")
        for it in recent.load():
            lb.insert("end", f"[{it.get('tool', '?')}] {it.get('path', '')}")
    except Exception:
        pass


def _succeeded(tool, result_label, say, btn):
    """Callback sukses terpusat: log + ingat dir + catat recent + refresh."""
    say(f"Selesai: {result_label}")
    _remember(result_label if os.path.isfile(result_label) else os.path.dirname(result_label))
    recent.add(tool, result_label)
    try:
        # refresh via event loop utama (thread-safe)
        _recent_lb.after(0, refresh_recent)  # type: ignore[union-attr]
    except Exception:
        refresh_recent()
    _busy_btn(btn, False)


def _tool_window(app, title, body_builder):
    import tkinter as tk
    win = tk.Toplevel(app)
    win.title(title)
    win.geometry("560x520")
    win.minsize(480, 420)
    log = tk.Text(win, height=6, state="disabled")
    import ttkbootstrap as ttk

    def say(msg):
        log.configure(state="normal")
        log.insert("end", msg + "\n")
        log.see("end")
        log.configure(state="disabled")

    frm = ttk.Frame(win, padding=10)
    frm.pack(fill="both", expand=True)
    body_builder(win, frm, say)
    log.pack(fill="x", padx=10, pady=(0, 10))
    return win


def _busy_btn(btn, busy=True):
    try:
        btn.configure(state="disabled" if busy else "normal")
    except Exception:
        pass


# ---------------------------------------------------------------- bodies
def body_merge(win, frm, say):
    import ttkbootstrap as ttk
    from src.ui.widgets import make_drop_listbox, run_async
    dz, lb, files = make_drop_listbox(frm)
    dz.pack(fill="both", expand=True)
    prev_box = ttk.Frame(frm)
    prev_box.pack(fill="x")

    def preview():
        for w in prev_box.winfo_children():
            w.destroy()
        if not files:
            return say("Daftar masih kosong.")
        import tkinter as tk
        from src.ui.thumbs import thumb_strip
        try:
            info = pdf_ops.pdf_info(files[0])
            say(f"Preview: {os.path.basename(files[0])} ({info['pages']} hal)")
            thumb_strip(prev_box, files[0], max_pages=6)
        except Exception as e:  # noqa: BLE001
            say(f"Preview gagal: {e}")
    ttk.Button(frm, text="👁 Preview file pertama", bootstyle="link",
               command=preview).pack(anchor="e")
    btn = ttk.Button(frm, text="Gabung → simpan PDF", bootstyle="primary")
    btn.pack(fill="x", pady=8)

    def go():
        out = _ask_out("gabungan.pdf")
        if not out:
            return
        _remember(out)
        _busy_btn(btn)
        say("Menggabung...")
        run_async(lambda: pdf_ops.merge_pdfs(list(files), out),
                  lambda r: _succeeded("Merge", r, say, btn),
                  lambda e: (say(f"Gagal: {e}"), _busy_btn(btn, False)))
    btn.configure(command=go)


def body_split(win, frm, say):
    import ttkbootstrap as ttk
    from tkinter import filedialog
    from src.ui.widgets import run_async
    src = {"p": ""}
    row = ttk.Frame(frm)
    row.pack(fill="x")
    import tkinter as tk
    lbl = ttk.Label(row, text="Belum ada file")
    lbl.pack(side="left", fill="x", expand=True)
    spec = tk.StringVar(value="per-halaman")

    def pick():
        p = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if p:
            src["p"] = p
            _remember(p)
            lbl.configure(text=os.path.basename(p))
            for w in prev_box.winfo_children():
                w.destroy()
            from src.ui.thumbs import thumb_strip
            try:
                info = pdf_ops.pdf_info(p)
                say(f"{info['pages']} halaman terdeteksi.")
                thumb_strip(prev_box, p, max_pages=8)
            except Exception as e:  # noqa: BLE001
                say(f"Preview gagal: {e}")
    ttk.Button(row, text="Pilih PDF", command=pick).pack(side="right")
    ttk.Label(frm, text="Mode (per-halaman / 1-3;4-5 / 1,3,5):").pack(anchor="w", pady=(8, 0))
    ttk.Entry(frm, textvariable=spec).pack(fill="x")
    prev_box = ttk.Frame(frm)
    prev_box.pack(fill="x", pady=4)
    btn = ttk.Button(frm, text="Pecah → folder", bootstyle="success")
    btn.pack(fill="x", pady=8)

    def go():
        if not src["p"]:
            return say("Pilih PDF dulu.")
        d = filedialog.askdirectory() or (os.path.dirname(src["p"]))
        _busy_btn(btn)
        say("Memecah...")
        run_async(lambda: pdf_ops.split_pdf(src["p"], d, spec.get().strip()),
                  lambda r: (_succeeded("Split", r[0] if r else d, say, btn),
                             say(f"Total {len(r)} file di: {d}")),
                  lambda e: (say(f"Gagal: {e}"), _busy_btn(btn, False)))
    btn.configure(command=go)


def _single_file_body(frm, say, btn_text, btn_style, fn, need_spec=False,
                      need_extra=None, tool="Tool"):
    """Generator umum: 1 file PDF + (opsional spec halaman + opsi) -> 1 output."""
    import tkinter as tk
    import ttkbootstrap as ttk
    from tkinter import filedialog
    from src.ui.widgets import run_async
    src = {"p": ""}
    vals = {}
    row = ttk.Frame(frm)
    row.pack(fill="x")
    lbl = ttk.Label(row, text="Belum ada file")
    lbl.pack(side="left", fill="x", expand=True)

    def pick():
        p = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf"), ("Semua", "*.*")])
        if p:
            src["p"] = p
            _remember(p)
            lbl.configure(text=os.path.basename(p))
    ttk.Button(row, text="Pilih file", command=pick).pack(side="right")
    spec_var = tk.StringVar(value="*")
    if need_spec:
        ttk.Label(frm, text="Halaman (* = semua, contoh 1-3,5):").pack(anchor="w", pady=(8, 0))
        ttk.Entry(frm, textvariable=spec_var).pack(fill="x")
    if need_extra:
        need_extra(frm, vals)
    btn = ttk.Button(frm, text=btn_text, bootstyle=btn_style)
    btn.pack(fill="x", pady=8)

    def go():
        if not src["p"]:
            return say("Pilih file dulu.")
        out = _ask_out("hasil.pdf")
        if not out:
            return
        _remember(out)
        args = dict(vals)
        for k, v in list(args.items()):
            if hasattr(v, "get"):
                args[k] = v.get()
        _busy_btn(btn)
        say("Memproses...")
        run_async(lambda: fn(src["p"], out, **args,
                             **({"spec": spec_var.get()} if need_spec else {})),
                  lambda r: _succeeded(tool, r if isinstance(r, str) else r.get("output", out), say, btn),
                  lambda e: (say(f"Gagal: {e}"), _busy_btn(btn, False)))
    btn.configure(command=go)


def _compress_extra(frm, vals):
    import tkinter as tk
    import ttkbootstrap as ttk
    vals["image_quality"] = tk.IntVar(value=60)
    vals["scale"] = tk.DoubleVar(value=0.8)
    ttk.Label(frm, text="Kualitas JPEG (1-95):").pack(anchor="w")
    ttk.Scale(frm, from_=20, to=90, variable=vals["image_quality"],
              orient="horizontal").pack(fill="x")
    ttk.Label(frm, text="Skala gambar (0.3-1.0):").pack(anchor="w")
    ttk.Scale(frm, from_=0.3, to=1.0, variable=vals["scale"],
              orient="horizontal").pack(fill="x")


def body_pdf2img(win, frm, say):
    import tkinter as tk
    import ttkbootstrap as ttk
    from tkinter import filedialog
    from src.ui.widgets import run_async
    src = {"p": ""}
    row = ttk.Frame(frm)
    row.pack(fill="x")
    lbl = ttk.Label(row, text="Belum ada file")
    lbl.pack(side="left", fill="x", expand=True)

    def pick():
        p = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if p:
            src["p"] = p
            _remember(p)
            lbl.configure(text=os.path.basename(p))
    ttk.Button(row, text="Pilih PDF", command=pick).pack(side="right")
    dpi = tk.IntVar(value=150)
    fmt = tk.StringVar(value="png")
    ttk.Label(frm, text="DPI (36-300):").pack(anchor="w", pady=(8, 0))
    ttk.Entry(frm, textvariable=dpi).pack(fill="x")
    ttk.Label(frm, text="Format:").pack(anchor="w")
    ttk.Combobox(frm, textvariable=fmt, values=["png", "jpg"], state="readonly").pack(fill="x")
    btn = ttk.Button(frm, text="Convert → folder", bootstyle="secondary")
    btn.pack(fill="x", pady=8)

    def go():
        if not src["p"]:
            return say("Pilih PDF dulu.")
        d = filedialog.askdirectory() or os.path.dirname(src["p"])
        _busy_btn(btn)
        say("Convert...")
        run_async(lambda: pdf_ops.pdf_to_images(src["p"], d, int(dpi.get()), fmt.get()),
                  lambda r: (_succeeded("PDF→Img", r[0] if r else d, say, btn),
                             say(f"Total {len(r)} gambar di: {d}")),
                  lambda e: (say(f"Gagal: {e}"), _busy_btn(btn, False)))
    btn.configure(command=go)


def body_img2pdf(win, frm, say):
    import ttkbootstrap as ttk
    from src.ui.widgets import make_drop_listbox, run_async
    dz, lb, files = make_drop_listbox(frm)
    dz.pack(fill="both", expand=True)
    btn = ttk.Button(frm, text="Jadikan PDF", bootstyle="primary")
    btn.pack(fill="x", pady=8)

    def go():
        out = _ask_out("dari-gambar.pdf")
        if not out:
            return
        _remember(out)
        _busy_btn(btn)
        say("Membuat PDF...")
        run_async(lambda: pdf_ops.images_to_pdf(list(files), out),
                  lambda r: _succeeded("Img→PDF", r, say, btn),
                  lambda e: (say(f"Gagal: {e}"), _busy_btn(btn, False)))
    btn.configure(command=go)


def body_watermark(win, frm, say):
    import tkinter as tk
    extra = {}
    def _ex(f, v):
        import ttkbootstrap as ttk
        v["text"] = tk.StringVar(value="DRAF")
        ttk.Label(f, text="Teks:").pack(anchor="w")
        ttk.Entry(f, textvariable=v["text"]).pack(fill="x")
        extra.update(v)
    _single_file_body(frm, say, "Tambah watermark", "dark",
                      lambda p, o, text="DRAF": pdf_ops.add_watermark(p, o, text),
                      need_extra=lambda f, v: _ex(f, v), tool="Watermark")


def body_protect(win, frm, say):
    import tkinter as tk
    def _ex(f, v):
        import ttkbootstrap as ttk
        v["user_pw"] = tk.StringVar()
        v["owner_pw"] = tk.StringVar()
        ttk.Label(f, text="Password:").pack(anchor="w")
        ttk.Entry(f, textvariable=v["user_pw"], show="•").pack(fill="x")
    _single_file_body(frm, say, "Kunci PDF", "warning",
                      lambda p, o, user_pw="", owner_pw="": pdf_ops.protect_pdf(p, o, user_pw, owner_pw or user_pw),
                      need_extra=_ex, tool="Protect")


def body_unlock(win, frm, say):
    import tkinter as tk
    def _ex(f, v):
        import ttkbootstrap as ttk
        v["password"] = tk.StringVar()
        ttk.Label(f, text="Password:").pack(anchor="w")
        ttk.Entry(f, textvariable=v["password"], show="•").pack(fill="x")
    _single_file_body(frm, say, "Buka kunci", "success",
                      lambda p, o, password="": pdf_ops.unlock_pdf(p, o, password),
                      need_extra=_ex, tool="Unlock")


def body_metadata(win, frm, say):
    import tkinter as tk
    import ttkbootstrap as ttk
    from tkinter import filedialog
    from src.ui.widgets import run_async
    src = {"p": ""}
    title, author, subject = tk.StringVar(), tk.StringVar(), tk.StringVar()
    row = ttk.Frame(frm)
    row.pack(fill="x")
    lbl = ttk.Label(row, text="Belum ada file")
    lbl.pack(side="left", fill="x", expand=True)

    def pick():
        p = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if p:
            src["p"] = p
            _remember(p)
            lbl.configure(text=os.path.basename(p))
            try:
                m = pdf_ops.get_metadata(p)
                title.set(m.get("title", ""))
                author.set(m.get("author", ""))
                subject.set(m.get("subject", ""))
                say(f"Metadata terbaca ({m.get('pages', '')} info).")
            except Exception as e:
                say(f"Gagal baca: {e}")
    ttk.Button(row, text="Pilih PDF", command=pick).pack(side="right")
    for lab, var in (("Judul:", title), ("Penulis:", author), ("Subjek:", subject)):
        ttk.Label(frm, text=lab).pack(anchor="w")
        ttk.Entry(frm, textvariable=var).pack(fill="x")
    btn = ttk.Button(frm, text="Simpan metadata", bootstyle="info")
    btn.pack(fill="x", pady=8)

    def go():
        if not src["p"]:
            return say("Pilih PDF dulu.")
        out = _ask_out("metadata.pdf")
        if not out:
            return
        _busy_btn(btn)
        meta = {"title": title.get(), "author": author.get(), "subject": subject.get()}
        run_async(lambda: pdf_ops.set_metadata(src["p"], out, meta),
                  lambda r: _succeeded("Metadata", r, say, btn),
                  lambda e: (say(f"Gagal: {e}"), _busy_btn(btn, False)))
    btn.configure(command=go)


def body_ocr(win, frm, say):
    import tkinter as tk
    import ttkbootstrap as ttk
    from tkinter import filedialog
    from src.ui.widgets import run_async
    st = ocr_ops.status()
    if st["available"]:
        ttk.Label(frm, text=f"✓ Tesseract siap: {st['exe']}\nBahasa: {', '.join(st['langs']) or '?'}",
                  bootstyle="success").pack(anchor="w", pady=4)
    else:
        ttk.Label(frm, text="✗ Tesseract belum ada.\nLihat plugins/ocr-README.md:\n"
                            "isi plugins/tesseract/ + tessdata ind+eng.",
                  bootstyle="danger").pack(anchor="w", pady=4)
    src = {"p": ""}
    lang = tk.StringVar(value="ind+eng")
    dpi = tk.IntVar(value=300)
    row = ttk.Frame(frm)
    row.pack(fill="x", pady=4)
    lbl = ttk.Label(row, text="Belum ada PDF scan")
    lbl.pack(side="left", fill="x", expand=True)

    def pick():
        p = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if p:
            src["p"] = p
            _remember(p)
            lbl.configure(text=os.path.basename(p))
    ttk.Button(row, text="Pilih PDF", command=pick).pack(side="right")
    ttk.Label(frm, text="Bahasa (contoh ind, eng, ind+eng):").pack(anchor="w")
    ttk.Entry(frm, textvariable=lang).pack(fill="x")
    ttk.Label(frm, text="DPI render (200-400 disarankan):").pack(anchor="w")
    ttk.Entry(frm, textvariable=dpi).pack(fill="x")
    btn = ttk.Button(frm, text="OCR → PDF searchable", bootstyle="info")
    btn.pack(fill="x", pady=8)

    def go():
        if not src["p"]:
            return say("Pilih PDF dulu.")
        out = _ask_out("searchable.pdf")
        if not out:
            return
        _busy_btn(btn)
        say("OCR berjalan (bisa menit untuk scan tebal)...")
        L, D = lang.get().strip() or "ind+eng", int(dpi.get())

        def _task():
            return ocr_ops.ocr_pdf_to_searchable(
                src["p"], out, lang=L, dpi=D,
                progress=lambda i, t: say(f"Hal {i}/{t}..."))
        run_async(_task,
                  lambda r: _succeeded("OCR", r, say, btn),
                  lambda e: (say(f"Gagal: {e}"), _busy_btn(btn, False)))
    btn.configure(command=go)


BUILDERS = {
    "Merge": body_merge, "Split": body_split,
    "Rotate": lambda w, f, s: _single_file_body(
        f, s, "Putar 90°", "info",
        lambda p, o: pdf_ops.rotate_pdf(p, o, 90), need_spec=True, tool="Rotate"),
    "Hapus/Extract": lambda w, f, s: _single_file_body(
        f, s, "Hapus halaman tsb", "warning",
        lambda p, o, spec="": pdf_ops.delete_pages(p, o, spec), need_spec=True, tool="Hapus"),
    "Compress": lambda w, f, s: _single_file_body(
        f, s, "Compress", "danger", pdf_ops.compress_pdf, need_extra=_compress_extra, tool="Compress"),
    "Img→PDF": body_img2pdf, "PDF→Img": body_pdf2img,
    "Watermark": body_watermark,
    "Nomor": lambda w, f, s: _single_file_body(
        f, s, "Tambah nomor", "light", pdf_ops.add_page_numbers, tool="Nomor"),
    "Metadata": body_metadata, "Protect": body_protect, "Unlock": body_unlock,
    "OCR": body_ocr,
}


def _splash(app):
    """Splash ringan tanpa file tambahan (tutup otomatis ~1,2 dtk)."""
    import tkinter as tk
    sp = tk.Toplevel(app)
    sp.overrideredirect(True)
    w, h = 320, 150
    sp.geometry(f"{w}x{h}+{(sp.winfo_screenwidth() - w) // 2}+{(sp.winfo_screenheight() - h) // 2}")
    sp.configure(bg="#26418f")
    tk.Label(sp, text="⧉ PDFTool Portable", font=("Segoe UI", 16, "bold"),
             bg="#26418f", fg="white").pack(pady=(28, 4))
    tk.Label(sp, text="multitool PDF offline • v1.0", font=("Segoe UI", 10),
             bg="#26418f", fg="#cfe0ff").pack()
    tk.Label(sp, text="memuat...", font=("Segoe UI", 9, "italic"),
             bg="#26418f", fg="#9db8e8").pack(pady=(10, 0))
    sp.after(1200, sp.destroy)
    return sp


def main():
    import ttkbootstrap as ttk
    s = settings.load()
    app = ttk.Window(themename=s.get("theme", "darkly"))
    app.title("PDFTool Portable — multitool PDF offline")
    app.geometry("760x640")
    app.minsize(640, 480)
    try:  # ikon window (diabaikan bila file tak ada)
        import tkinter as tk
        ico_png = settings.resource_path(os.path.join("assets", "icon.png"))
        if os.path.isfile(ico_png):
            _ph = tk.PhotoImage(file=ico_png).subsample(8, 8)  # 256 -> 32
            app.iconphoto(True, _ph)
            app._icon_ref = _ph  # tahan dari GC
    except Exception:
        pass
    _splash(app)

    ttk.Label(app, text="PDFTool Portable", font=("Segoe UI", 16, "bold")).pack(pady=(12, 2))
    try:
        st = ocr_ops.status()
        ocr_txt = "OCR ✓ siap" if st["available"] else "OCR ✗ belum (lihat plugins/ocr-README.md)"
    except Exception:
        ocr_txt = "OCR ?"
    ttk.Label(app, text=f"100% offline • tanpa upload • {ocr_txt}").pack(pady=(0, 10))

    grid = ttk.Frame(app, padding=10)
    grid.pack(fill="both", expand=True)
    for i in range(4):
        grid.columnconfigure(i, weight=1)

    for idx, (icon, name, desc, style) in enumerate(TOOLS):
        card = ttk.Button(
            grid, text=f"{icon}\n{name}\n{desc}", bootstyle=f"{style}-outline",
            command=lambda n=name: _tool_window(app, n, BUILDERS[n]))
        card.grid(row=idx // 4, column=idx % 4, padx=6, pady=6, sticky="nsew", ipady=14)
        grid.rowconfigure(idx // 4, weight=1)

    # riwayat hasil (portable, data/recent.json)
    global _recent_lb
    import tkinter as tk
    rec_frm = ttk.Frame(app, padding=(10, 0))
    rec_frm.pack(fill="x")
    ttk.Label(rec_frm, text="Terakhir diproses (klik 2x = buka folder):",
              font=("Segoe UI", 9, "bold")).pack(anchor="w")
    _recent_lb = tk.Listbox(rec_frm, height=3)
    _recent_lb.pack(fill="x", pady=(2, 4))
    refresh_recent()

    def _open_recent(_ev=None):
        sel = _recent_lb.curselection()
        if not sel:
            return
        txt = _recent_lb.get(sel[0])
        path = txt.split("] ", 1)[1] if "] " in txt else txt
        folder = path if os.path.isdir(path) else os.path.dirname(path)
        try:
            if sys.platform.startswith("win"):
                os.startfile(folder)  # noqa: S606
            elif sys.platform == "darwin":
                import subprocess
                subprocess.Popen(["open", folder])
            else:
                import subprocess
                subprocess.Popen(["xdg-open", folder])
        except Exception:
            pass
    _recent_lb.bind("<Double-Button-1>", _open_recent)

    # toggle tema
    def _theme():
        ns = settings.load()
        ns["theme"] = "flatly" if ns.get("theme") == "darkly" else "darkly"
        settings.save(ns)
        app.style.theme_use(ns["theme"])
    bot = ttk.Frame(app)
    bot.pack(pady=(0, 10))
    ttk.Button(bot, text="🌙/☀ Ganti tema", bootstyle="link",
               command=_theme).pack(side="left", padx=8)
    ttk.Button(bot, text="🧹 Bersihkan riwayat", bootstyle="link",
               command=lambda: (recent.clear(), refresh_recent())).pack(side="left", padx=8)
    if os.environ.get("PDFTOOL_SMOKE"):
        # hook test headless: tutup otomatis agar binary bisa di-smoke-test
        app.after(3000, app.destroy)
    app.mainloop()


if __name__ == "__main__":
    main()
