"""Test GUI headless (butuh xvfb): buka dashboard + ke-14 tool window,
plus alur fungsional Atur Halaman (pilih PDF, klik seleksi, drag pindah).

Jalankan: source dev-env.sh && xvfb-run -a python3 tests/test_gui.py
Menangkap NameError/typo di semua body builder tanpa klik manual.
"""
import os
import re
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import src.main as M

TMP = os.path.join(os.path.dirname(__file__), "tmp")
TAG_RE = re.compile(r"^\d+( • \d+°)?( \(\+\d+\))?$")


def main():
    import ttkbootstrap as ttk
    app = ttk.Window(themename="darkly")
    app.withdraw()
    assert len(M.TOOLS) == 14, f"kartu dashboard {len(M.TOOLS)} != 14"
    assert set(M.BUILDERS) == {t[1] for t in M.TOOLS}, "BUILDERS vs TOOLS tidak sinkron"

    msgs = []

    def say(m):
        msgs.append(m)

    import tkinter as tk
    for _icon, name, _desc, _style in M.TOOLS:
        frm = ttk.Frame(app)
        frm.pack()
        try:
            M.BUILDERS[name](app, frm, say)
        except Exception as e:  # noqa: BLE001
            raise SystemExit(f"Tool {name} gagal dibangun: {type(e).__name__}: {e}")
        frm.destroy()
        print(f"window {name} OK")
    # splash juga harus bisa dibangun
    sp = M._splash(app)
    sp.update()
    sp.destroy()
    _test_organize_flow(app, say)
    app.destroy()
    print("TEST GUI LOLOS")


def _walk(w):
    yield w
    for ch in w.winfo_children():
        yield from _walk(ch)


def _find_btn(root, text):
    import tkinter as tk  # noqa: F401
    for w in _walk(root):
        if w.winfo_class() == "TButton" and w.cget("text") == text:
            return w
    return None


def _tags(root):
    return [w for w in _walk(root)
            if w.winfo_class() == "Label" and TAG_RE.match(str(w.cget("text") or ""))]


def _test_organize_flow(app, say):
    """Alur nyata: pilih PDF 4 hal -> klik seleksi -> drag pindah -> putar."""
    import time as _t
    import tkinter as tk
    import tkinter.filedialog as fd
    import ttkbootstrap as ttk
    import pymupdf

    os.makedirs(TMP, exist_ok=True)
    fun = os.path.join(TMP, "fun.pdf")
    d = pymupdf.open()
    for i in range(4):
        d.new_page().insert_text((72, 72), f"H{i + 1}")
    d.save(fun)
    d.close()

    frm = ttk.Frame(app)
    frm.pack()
    M.BUILDERS["Atur"](app, frm, say)
    app.update()

    orig = fd.askopenfilename
    fd.askopenfilename = lambda **k: fun
    try:
        _find_btn(frm, "Pilih PDF").invoke()
    finally:
        fd.askopenfilename = orig

    # tunggu thread thumbnail (maks 20 dtk)
    tags = []
    for _ in range(200):
        app.update()
        tags = _tags(frm)
        if len(tags) >= 4:
            break
        _t.sleep(0.1)
    assert len(tags) >= 4, f"thumbnail tak muncul: {len(tags)}"
    order = [t.cget("text") for t in tags]
    assert order[0].startswith("1"), f"urutan awal salah: {order}"
    print(f"atur: load 4 hal OK {order}")

    # klik sel pertama -> seleksi
    tags[0].event_generate("<ButtonPress-1>", x=5, y=5)
    tags[0].event_generate("<ButtonRelease-1>", x=5, y=5)
    app.update()

    # drag sel pertama ke posisi ketiga
    tags = _tags(frm)
    tags[0].event_generate("<ButtonPress-1>", x=5, y=5)
    app.update()
    tags[0].event_generate("<B1-Motion>", x=300, y=5)
    app.update()
    tags = _tags(frm)
    tags[2].event_generate("<ButtonRelease-1>", x=5, y=5)
    app.update()
    order = [t.cget("text") for t in _tags(frm)]
    assert order[0].startswith("2"), f"drag gagal: {order}"
    print(f"atur: drag 1->3 OK {order}")

    # putar yang terseleksi (sekarang posisi 2 = hal 1) 90°
    _find_btn(frm, "⟳").invoke()
    app.update()
    order = [t.cget("text") for t in _tags(frm)]
    assert "90°" in order[2], f"putar gagal: {order}"
    print(f"atur: rotate OK {order}")

    # hapus yang terseleksi -> sisa 3
    _find_btn(frm, "✕ Hapus").invoke()
    app.update()
    assert len(_tags(frm)) == 3, "hapus gagal"
    print("atur: delete OK sisa 3")
    frm.destroy()


if __name__ == "__main__":
    main()
