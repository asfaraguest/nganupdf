"""NganuPDF — dashboard grid ala PDF24 (tkinter + ttkbootstrap)."""
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
    ("☰", "Atur", "Susun ulang halaman", "dark"),
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


def _is_dark() -> bool:
    try:
        return settings.load().get("theme", "darkly") != "flatly"
    except Exception:
        return True


def _tool_icon(name: str) -> str:
    for icon, tname, _d, _s in TOOLS:
        if tname == name:
            return icon
    return "⧉"


def _tool_desc(name: str) -> str:
    for _i, tname, desc, _s in TOOLS:
        if tname == name:
            return desc
    return ""


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
    win.title(f"NganuPDF — {title}")
    win.geometry("600x560")
    win.minsize(500, 440)
    import ttkbootstrap as ttk

    # header tool: ikon besar + judul + deskripsi
    head = ttk.Frame(win, padding=(14, 12, 14, 4))
    head.pack(fill="x")
    tk.Label(head, text=_tool_icon(title), font=("Segoe UI", 26)).pack(side="left", padx=(0, 12))
    cap = ttk.Frame(head)
    cap.pack(side="left", fill="x", expand=True)
    ttk.Label(cap, text=title, font=("Segoe UI", 14, "bold")).pack(anchor="w")
    ttk.Label(cap, text=_tool_desc(title), font=("Segoe UI", 9)).pack(anchor="w")
    ttk.Separator(win).pack(fill="x", padx=14, pady=(6, 2))

    dark = _is_dark()
    log = tk.Text(win, height=6, state="disabled", relief="flat",
                  font=("Consolas", 9),
                  bg="#1e1e1e" if dark else "#f4f4f4",
                  fg="#d4d4d4" if dark else "#222222",
                  insertbackground="#d4d4d4" if dark else "#222222")

    def say(msg):
        log.configure(state="normal")
        log.insert("end", msg + "\n")
        log.see("end")
        log.configure(state="disabled")

    frm = ttk.Frame(win, padding=(14, 6, 14, 6))
    frm.pack(fill="both", expand=True)
    body_builder(win, frm, say)
    log.pack(fill="x", padx=14, pady=(4, 12))
    return win


def _busy_btn(btn, busy=True):
    """Kunci tombol saat proses + teks ⏳ agar jelas sedang bekerja."""
    try:
        if busy:
            if not hasattr(btn, "_txt"):
                btn._txt = btn.cget("text")  # type: ignore[attr-defined]
            btn.configure(state="disabled", text="⏳ Memproses…", cursor="watch")
        else:
            btn.configure(state="normal", cursor="hand2")
            if hasattr(btn, "_txt"):
                btn.configure(text=btn._txt)  # type: ignore[attr-defined]
    except Exception:
        try:
            btn.configure(state="disabled" if busy else "normal")
        except Exception:
            pass


def _act_btn(parent, text, bootstyle="primary"):
    """Tombol aksi utama yang konsisten: gemuk, pointer tangan."""
    import ttkbootstrap as ttk
    return ttk.Button(parent, text=text, bootstyle=bootstyle,
                      padding=(14, 10), cursor="hand2")


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
    btn = _act_btn(frm, "Gabung → simpan PDF", "primary")
    btn.pack(fill="x", pady=8)

    def go():
        out = _ask_out("gabungan.pdf")
        if not out:
            return
        _remember(out)
        _busy_btn(btn)
        say("Menggabung...")
        run_async(frm, lambda: pdf_ops.merge_pdfs(list(files), out),
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
    btn = _act_btn(frm, "Pecah → folder", "success")
    btn.pack(fill="x", pady=8)

    def go():
        if not src["p"]:
            return say("Pilih PDF dulu.")
        d = filedialog.askdirectory() or (os.path.dirname(src["p"]))
        _busy_btn(btn)
        say("Memecah...")
        run_async(frm, lambda: pdf_ops.split_pdf(src["p"], d, spec.get().strip()),
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
    btn = _act_btn(frm, btn_text, btn_style)
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
        run_async(frm, lambda: fn(src["p"], out, **args,
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
    btn = _act_btn(frm, "Convert → folder", "secondary")
    btn.pack(fill="x", pady=8)

    def go():
        if not src["p"]:
            return say("Pilih PDF dulu.")
        d = filedialog.askdirectory() or os.path.dirname(src["p"])
        _busy_btn(btn)
        say("Convert...")
        run_async(frm, lambda: pdf_ops.pdf_to_images(src["p"], d, int(dpi.get()), fmt.get()),
                  lambda r: (_succeeded("PDF→Img", r[0] if r else d, say, btn),
                             say(f"Total {len(r)} gambar di: {d}")),
                  lambda e: (say(f"Gagal: {e}"), _busy_btn(btn, False)))
    btn.configure(command=go)


def body_img2pdf(win, frm, say):
    import ttkbootstrap as ttk
    from src.ui.widgets import make_drop_listbox, run_async
    dz, lb, files = make_drop_listbox(frm)
    dz.pack(fill="both", expand=True)
    btn = _act_btn(frm, "Jadikan PDF", "primary")
    btn.pack(fill="x", pady=8)

    def go():
        out = _ask_out("dari-gambar.pdf")
        if not out:
            return
        _remember(out)
        _busy_btn(btn)
        say("Membuat PDF...")
        run_async(frm, lambda: pdf_ops.images_to_pdf(list(files), out),
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
    btn = _act_btn(frm, "Simpan metadata", "info")
    btn.pack(fill="x", pady=8)

    def go():
        if not src["p"]:
            return say("Pilih PDF dulu.")
        out = _ask_out("metadata.pdf")
        if not out:
            return
        _busy_btn(btn)
        meta = {"title": title.get(), "author": author.get(), "subject": subject.get()}
        run_async(frm, lambda: pdf_ops.set_metadata(src["p"], out, meta),
                  lambda r: _succeeded("Metadata", r, say, btn),
                  lambda e: (say(f"Gagal: {e}"), _busy_btn(btn, False)))
    btn.configure(command=go)


def body_organize(win, frm, say):
    """Atur Halaman ala iLovePDF Organize: thumbnail grid + drag-drop
    susun ulang, putar, hapus, tambah dari PDF lain. Tanpa render ulang
    saat simpan (vektor tetap tajam)."""
    import tkinter as tk
    import ttkbootstrap as ttk
    from tkinter import filedialog
    from src.ui.widgets import run_async

    COLS, MAXW, CAP = 4, 140, 300
    SRC_COLORS = ["#1f6feb", "#1a7f37", "#9e6a03", "#8957e5", "#cf222e", "#0a7ea4"]
    st = {"primary": "", "extras": [], "items": [], "snap": [],
          "sel": set(), "anchor": 0, "thumbs": {}, "drag": None}
    refs = []

    top = ttk.Frame(frm)
    top.pack(fill="x")
    name_lbl = ttk.Label(top, text="Belum ada PDF — pilih atau seret file ke sini",
                         font=("Segoe UI", 9, "bold"))
    name_lbl.pack(side="left", fill="x", expand=True)
    cnt_lbl = ttk.Label(top, text="")
    cnt_lbl.pack(side="right")
    legend = ttk.Label(frm, text="", font=("Segoe UI", 8), wraplength=520)
    legend.pack(anchor="w")

    def _legend():
        if not st["primary"]:
            legend.configure(text="")
            return
        parts = [f"[0] {os.path.basename(st['primary'])}"]
        parts += [f"[{i + 1}] {os.path.basename(p)}" for i, p in enumerate(st["extras"])]
        legend.configure(text="Sumber: " + "   ".join(parts))

    cv_box = ttk.Frame(frm)
    cv_box.pack(fill="both", expand=True, pady=4)
    cv = tk.Canvas(cv_box, highlightthickness=0)
    sb = ttk.Scrollbar(cv_box, orient="vertical", command=cv.yview)
    cv.configure(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y")
    cv.pack(side="left", fill="both", expand=True)
    inner = ttk.Frame(cv)
    cv.create_window((0, 0), window=inner, anchor="nw")
    inner.bind("<Configure>", lambda _e: cv.configure(scrollregion=cv.bbox("all")))

    def _load_thumbs():
        from PIL import Image
        import io as _io
        import pymupdf as _fitz
        st["thumbs"] = thumbs = {}
        files = [st["primary"], *st["extras"]] if st["primary"] else []
        if not files:
            return
        need = {(s, o) for (s, o, _r) in st["items"][:CAP]}
        docs = [_fitz.open(p) for p in files]
        try:
            for (s, o) in need:
                if (s, o) in thumbs or not 0 <= s < len(docs):
                    continue
                pg = docs[s][o]
                z = min(max(MAXW / max(1.0, pg.rect.width), 0.1), 3.0)
                pix = pg.get_pixmap(matrix=_fitz.Matrix(z, z))
                thumbs[(s, o)] = Image.open(_io.BytesIO(pix.tobytes("png"))).convert("RGB")
        finally:
            for d in docs:
                d.close()

    def refresh():
        for w in inner.winfo_children():
            w.destroy()
        refs.clear()
        n = len(st["items"])
        cnt_lbl.configure(text=f"{n} halaman" + (f" • {len(st['sel'])} dipilih" if st["sel"] else ""))
        shown = st["items"][:CAP]
        if n > CAP:
            say(f"Preview dibatasi {CAP} halaman pertama (simpan tetap full).")
        for pos, (s, o, r) in enumerate(shown):
            border = SRC_COLORS[s % len(SRC_COLORS)]
            base_hl = "#ffffff" if pos in st["sel"] else border
            cell = tk.Frame(inner, relief="sunken" if pos in st["sel"] else "groove",
                            borderwidth=2, highlightthickness=2,
                            highlightbackground=base_hl, cursor="hand2",
                            bg="#1f6feb" if pos in st["sel"] else None)
            cell.grid(row=pos // COLS, column=pos % COLS, padx=4, pady=4)
            im = st["thumbs"].get((s, o))
            if im is not None:
                disp = im.rotate(-r, expand=True) if r else im
                from src.ui.thumbs import to_tk
                try:
                    ph = to_tk(disp)
                    refs.append(ph)
                    pic = tk.Label(cell, image=ph, bg=cell.cget("bg"))
                except Exception:
                    pic = tk.Label(cell, text=f"hal {o + 1}", width=18, height=8)
            else:
                pic = tk.Label(cell, text=f"hal {o + 1}", width=18, height=8)
            pic.pack()
            tag = f"{o + 1}{f' • {r}°' if r else ''}{f' (+{s})' if s else ''}"
            tk.Label(cell, text=tag, font=("Segoe UI", 8),
                     bg=cell.cget("bg")).pack()
            for wdg in (cell, pic):
                wdg.bind("<ButtonPress-1>", lambda e, p=pos: _press(p, e))
                wdg.bind("<B1-Motion>", _motion)
                wdg.bind("<ButtonRelease-1>", lambda e, p=pos: _release(p, e))
                wdg.bind("<Enter>", lambda e, c=cell, b=base_hl: c.configure(highlightbackground="#ffffff"))
                wdg.bind("<Leave>", lambda e, c=cell, b=base_hl: c.configure(highlightbackground=b))
        # bind label anak juga
        for cell in inner.winfo_children():
            _bh = cell.cget("highlightbackground")
            for ch in cell.winfo_children():
                ch.bind("<ButtonPress-1>", lambda e, p=cell.grid_info()["row"] * COLS + cell.grid_info()["column"]: _press(p, e))
                ch.bind("<B1-Motion>", _motion)
                ch.bind("<ButtonRelease-1>", lambda e, p=cell.grid_info()["row"] * COLS + cell.grid_info()["column"]: _release(p, e))
                ch.bind("<Enter>", lambda e, c=cell: c.configure(highlightbackground="#ffffff"))
                ch.bind("<Leave>", lambda e, c=cell, b=_bh: c.configure(highlightbackground=b))

    def _press(pos, ev):
        # Catat saja; JANGAN refresh di sini (widget sedang di-drag akan hancur).
        st["drag"] = {"from": pos, "x": ev.x_root, "y": ev.y_root, "move": False}
        if ev.state & 0x4:  # Ctrl
            st["sel"] ^= {pos}
            st["anchor"] = pos
        elif ev.state & 0x1 and st["anchor"] is not None:  # Shift
            a, b = sorted((st["anchor"], pos))
            st["sel"] = set(range(a, b + 1))
        else:
            st["_pending_sel"] = pos
            st["anchor"] = pos

    def _motion(ev):
        d = st.get("drag")
        if not d:
            return
        if abs(ev.x_root - d["x"]) + abs(ev.y_root - d["y"]) > 8:
            d["move"] = True

    def _release(pos, _ev):
        d = st.get("drag")
        st["drag"] = None
        if not d:
            return
        if not d["move"]:
            # klik murni: terapkan seleksi sekarang lalu refresh
            pending = st.pop("_pending_sel", None)
            if pending is not None and pending not in st["sel"]:
                st["sel"] = {pending}
            refresh()
            return
        src, dst = d["from"], pos
        if src == dst:
            refresh()
            return
        st.pop("_pending_sel", None)
        it = st["items"].pop(src)
        st["items"].insert(dst, it)
        st["sel"] = {dst}
        st["anchor"] = dst
        say(f"Pindah hal ke posisi {dst + 1}.")
        refresh()

    def _need_file():
        if not st["primary"]:
            say("Pilih PDF dulu.")
            return False
        return True

    def pick():
        p = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if not p:
            return
        _remember(p)
        st.update(primary=p, extras=[], sel=set(), anchor=0)
        try:
            n = pdf_ops.pdf_info(p)["pages"]
        except Exception as e:  # noqa: BLE001
            return say(f"Gagal baca: {e}")
        st["items"] = [(0, i, 0) for i in range(n)]
        st["snap"] = list(st["items"])
        name_lbl.configure(text=f"{os.path.basename(p)} ({n} hal)")
        _legend()
        say("Memuat thumbnail...")
        run_async(frm, _load_thumbs,
                  lambda _r: (refresh(), say("Siap. Seret thumbnail untuk susun ulang.")),
                  lambda e: say(f"Gagal: {e}"))

    def _add_paths(paths):
        """Tambah halaman dari file lain (dipakai tombol + drop Explorer)."""
        added = 0
        for p in paths:
            p = os.path.abspath(p)
            if not p.lower().endswith(".pdf") or not os.path.isfile(p):
                continue
            if p in st["extras"] or p == st["primary"]:
                say(f"Sudah ada: {os.path.basename(p)}.")
                continue
            try:
                n = pdf_ops.pdf_info(p)["pages"]
            except Exception as e:  # noqa: BLE001
                say(f"Lewati {os.path.basename(p)}: {e}")
                continue
            st["extras"].append(p)
            s = len(st["extras"])
            st["items"] += [(s, i, 0) for i in range(n)]
            added += n
            say(f"+{n} hal dari {os.path.basename(p)}.")
        if added:
            st["snap"] = list(st["items"])
            _legend()
            run_async(frm, _load_thumbs, lambda _r: refresh(), lambda e: say(f"Gagal: {e}"))
        return added

    def add_more():
        if not _need_file():
            return
        _add_paths(filedialog.askopenfilenames(filetypes=[("PDF", "*.pdf")]))

    def _on_drop(ev):
        # Drop dari Explorer: file pertama jadi utama bila kosong,
        # sisanya ditambah. Tanpa file utama, drop diabaikan berpesan.
        try:
            paths = [p.strip("{}") for p in win.splitlist(ev.data)]
        except Exception:
            return
        pdfs = [p for p in paths if p.lower().endswith(".pdf") and os.path.isfile(p)]
        if not pdfs:
            return say("Seret file .pdf ke sini.")
        if not st["primary"]:
            first, rest = pdfs[0], pdfs[1:]
            st.update(primary=os.path.abspath(first), extras=[], sel=set(), anchor=0)
            try:
                n = pdf_ops.pdf_info(first)["pages"]
            except Exception as e:  # noqa: BLE001
                st["primary"] = ""
                return say(f"Gagal baca: {e}")
            _remember(first)
            st["items"] = [(0, i, 0) for i in range(n)]
            st["snap"] = list(st["items"])
            name_lbl.configure(text=f"{os.path.basename(first)} ({n} hal)")
            _legend()
            say("Memuat thumbnail...")
            run_async(frm, _load_thumbs,
                      lambda _r: (_add_paths(rest), refresh(),
                                  say("Siap. Seret thumbnail untuk susun ulang.")),
                      lambda e: say(f"Gagal: {e}"))
        else:
            _add_paths(pdfs)

    try:  # aktif hanya bila root TkinterDnD (fallback: tombol tetap jalan)
        from tkinterdnd2 import DND_FILES
        win.drop_target_register(DND_FILES)
        win.dnd_bind("<<Drop>>", _on_drop)
    except Exception:
        pass

    def rotate_sel(dgr):
        if not _need_file() or not st["sel"]:
            return say("Klik dulu halaman yang mau diputar.")
        for pos in st["sel"]:
            s, o, r = st["items"][pos]
            st["items"][pos] = (s, o, (r + dgr) % 360)
        refresh()

    def delete_sel():
        if not _need_file() or not st["sel"]:
            return say("Klik dulu halaman yang mau dihapus.")
        for pos in sorted(st["sel"], reverse=True):
            del st["items"][pos]
        st["sel"] = set()
        say(f"Dihapus. Sisa {len(st['items'])} halaman.")
        refresh()

    def reset():
        if not _need_file():
            return
        st["items"] = list(st["snap"])
        st["sel"] = set()
        refresh()
        say("Urutan dikembalikan.")

    bar = ttk.Frame(frm)
    bar.pack(fill="x", pady=(0, 2))
    ttk.Button(bar, text="Pilih PDF", command=pick).pack(side="left")
    ttk.Button(bar, text="＋ Tambah PDF", command=add_more).pack(side="left", padx=4)
    ttk.Button(bar, text="⟲", width=4, command=lambda: rotate_sel(270)).pack(side="left")
    ttk.Button(bar, text="⟳", width=4, command=lambda: rotate_sel(90)).pack(side="left", padx=2)
    ttk.Button(bar, text="✕ Hapus", command=delete_sel).pack(side="left", padx=4)
    ttk.Button(bar, text="↺ Reset", command=reset).pack(side="right")
    btn = _act_btn(frm, "Simpan hasil → PDF", "primary")
    btn.pack(fill="x", pady=6)

    def go():
        if not _need_file() or not st["items"]:
            return say("Tidak ada halaman untuk disimpan.")
        out = _ask_out("organized.pdf")
        if not out:
            return
        _busy_btn(btn)
        say("Menyimpan...")
        items, extras, prim = list(st["items"]), list(st["extras"]), st["primary"]
        run_async(frm, lambda: pdf_ops.organize_pdfs(prim, out, items, extras),
                  lambda r: _succeeded("Atur", r, say, btn),
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
    btn = _act_btn(frm, "OCR → PDF searchable", "info")
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
        run_async(frm, _task,
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
    "OCR": body_ocr, "Atur": body_organize,
}


def _splash(app):
    """Splash: ikon besar + nama + progressbar (tutup otomatis ~1,4 dtk)."""
    import tkinter as tk
    import ttkbootstrap as ttk
    sp = tk.Toplevel(app)
    sp.overrideredirect(True)
    w, h = 360, 250
    sp.geometry(f"{w}x{h}+{(sp.winfo_screenwidth() - w) // 2}+{(sp.winfo_screenheight() - h) // 2}")
    sp.configure(bg="#1c2f6b")
    tk.Frame(sp, bg="#4c8dff", height=5).pack(fill="x")
    try:
        ico = settings.resource_path(os.path.join("assets", "icon.png"))
        if os.path.isfile(ico):
            _sp = tk.PhotoImage(file=ico).subsample(3, 3)  # 256 -> 85
            tk.Label(sp, image=_sp, bg="#1c2f6b").pack(pady=(16, 2))
            sp._icon_ref = _sp  # noqa: SLF001 (tahan dari GC)
    except Exception:
        pass
    tk.Label(sp, text="NganuPDF", font=("Segoe UI", 22, "bold"),
             bg="#1c2f6b", fg="white").pack()
    tk.Label(sp, text="Multitool PDF • 100% offline", font=("Segoe UI", 10),
             bg="#1c2f6b", fg="#cfe0ff").pack()
    pb = ttk.Progressbar(sp, mode="indeterminate", bootstyle="info-striped",
                         length=240)
    pb.pack(pady=(14, 0))
    pb.start(12)
    sp.after(1400, sp.destroy)
    return sp


def main():
    import ttkbootstrap as ttk
    s = settings.load()
    try:
        # Root DnD agar drop file dari Explorer aktif (Merge, Img->PDF, Atur).
        # Fallback ke Window biasa bila tkinterdnd2 tak ada.
        from tkinterdnd2 import TkinterDnD
        app = TkinterDnD.Tk()
        app.style = ttk.Style(theme=s.get("theme", "darkly"))
    except Exception:
        app = ttk.Window(themename=s.get("theme", "darkly"))
    app.title("NganuPDF — multitool PDF offline")
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

    # header: ikon + judul + status
    import tkinter as tk
    head = ttk.Frame(app, padding=(16, 14, 16, 2))
    head.pack(fill="x")
    try:
        _hico = tk.PhotoImage(file=ico_png).subsample(5, 5) if os.path.isfile(ico_png) else None
    except Exception:
        _hico = None
    if _hico is not None:
        ttk.Label(head, image=_hico).pack(side="left", padx=(0, 12))
        app._head_ref = _hico  # tahan dari GC
    cap = ttk.Frame(head)
    cap.pack(side="left", fill="x", expand=True)
    ttk.Label(cap, text="NganuPDF", font=("Segoe UI", 20, "bold")).pack(anchor="w")
    try:
        st = ocr_ops.status()
        ocr_txt = "OCR ✓ siap" if st["available"] else "OCR ✗ belum (lihat plugins/ocr-README.md)"
    except Exception:
        ocr_txt = "OCR ?"
    ttk.Label(cap, text=f"100% offline • tanpa upload • {ocr_txt}",
              font=("Segoe UI", 9)).pack(anchor="w")
    ttk.Separator(app).pack(fill="x", padx=16, pady=(8, 0))
    try:
        _accent = app.style.colors.get("primary")
    except Exception:
        _accent = "#1f6feb"
    tk.Frame(app, bg=_accent, height=2).pack(fill="x", padx=16, pady=(0, 2))

    grid = ttk.Frame(app, padding=10)
    grid.pack(fill="both", expand=True)
    for i in range(4):
        grid.columnconfigure(i, weight=1)

    def _make_card(parent, icon, name, desc, style):
        """Kartu tool custom: ikon besar + nama bold + deskripsi, hover glow."""
        try:
            accent = app.style.colors.get(style)
        except Exception:
            accent = "#1f6feb"
        base_bg = app.style.lookup("TFrame", "background") or ("#2b2b2b" if _is_dark() else "#ffffff")
        name_fg = "#f2f2f2" if _is_dark() else "#212121"
        shadow = tk.Frame(parent, bg="#000000")
        card = tk.Frame(shadow, bg=base_bg, relief="flat", borderwidth=0,
                        highlightthickness=1, highlightbackground=accent,
                        cursor="hand2")
        card.pack(fill="both", expand=True, padx=(0, 3), pady=(0, 3))
        strip = tk.Frame(card, bg=accent, height=4)
        strip.pack(fill="x")
        ic = tk.Label(card, text=icon, font=("Segoe UI", 26), bg=base_bg, fg=accent)
        ic = tk.Label(card, text=icon, font=("Segoe UI", 26), bg=base_bg, fg=accent)
        ic.pack(pady=(12, 0))
        nm = tk.Label(card, text=name, font=("Segoe UI", 11, "bold"), bg=base_bg, fg=name_fg)
        nm.pack()
        ds = tk.Label(card, text=desc, font=("Segoe UI", 8), bg=base_bg, fg="#8a8a8a")
        ds.pack(pady=(0, 12))
        orig_fg = {w: w.cget("fg") for w in (ic, nm, ds)}

        def _hover(on=True):
            card.configure(bg=accent if on else base_bg)
            for wdg in (ic, nm, ds):
                wdg.configure(bg=accent if on else base_bg,
                              fg="#ffffff" if on else orig_fg[wdg])

        def _open(_e=None):
            _tool_window(app, name, BUILDERS[name])

        for wdg in (card, strip, ic, nm, ds):
            wdg.bind("<Enter>", lambda e: _hover(on=True))
            wdg.bind("<Leave>", lambda e: _hover(on=False))
            wdg.bind("<Button-1>", _open)
        return shadow

    for idx, (icon, name, desc, style) in enumerate(TOOLS):
        _make_card(grid, icon, name, desc, style).grid(
            row=idx // 4, column=idx % 4, padx=6, pady=6, sticky="nsew")
        grid.rowconfigure(idx // 4, weight=1)

    # riwayat hasil (portable, data/recent.json)
    global _recent_lb
    import tkinter as tk
    rec_frm = ttk.Frame(app, padding=(10, 0))
    rec_frm.pack(fill="x")
    ttk.Label(rec_frm, text="Terakhir diproses (klik 2x = buka folder):",
              font=("Segoe UI", 9, "bold")).pack(anchor="w")
    _recent_lb = tk.Listbox(rec_frm, height=3, relief="flat",
                            font=("Segoe UI", 9),
                            bg="#1e1e1e" if _is_dark() else "#ffffff",
                            fg="#d4d4d4" if _is_dark() else "#212121",
                            selectbackground="#1f6feb", selectforeground="#ffffff",
                            highlightthickness=1)
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
