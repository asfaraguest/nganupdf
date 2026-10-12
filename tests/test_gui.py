"""Test GUI headless (butuh xvfb): buka dashboard + ke-13 tool window.

Jalankan: source dev-env.sh && xvfb-run -a python3 tests/test_gui.py
Menangkap NameError/typo di semua body builder tanpa klik manual.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import src.main as M


def main():
    import ttkbootstrap as ttk
    app = ttk.Window(themename="darkly")
    app.withdraw()
    assert len(M.TOOLS) == 13, f"kartu dashboard {len(M.TOOLS)} != 13"
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
    app.destroy()
    print("TEST GUI LOLOS")


if __name__ == "__main__":
    main()
