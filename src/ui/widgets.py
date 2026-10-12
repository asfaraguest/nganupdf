"""Widget reusable: DropZone (drag-drop), FileList, run_async worker."""
import os
import queue
import threading

# Semua callback UI HARUS jalan di main thread Tk. run_async menaruh
# hasilnya ke antrean ini; _pump (after-loop di main thread) mengeksekusinya.
_UIQ: queue.Queue = queue.Queue()


def _pump(widget):
    try:
        while True:
            cb = _UIQ.get_nowait()
            try:
                cb()
            except Exception:
                pass
    except queue.Empty:
        pass
    try:
        widget.after(100, lambda: _pump(widget))
    except Exception:
        pass


def run_async(widget, fn, on_done, on_error):
    """Jalankan fn() di thread agar UI tidak freeze.

    on_done/on_error selalu dieksekusi di MAIN thread (aman sentuh widget).
    widget = frame/window pemilik (untuk after-pump).
    """
    try:
        if not getattr(widget, "_pump_on", False):
            widget._pump_on = True  # type: ignore[attr-defined]
            widget.after(100, lambda: _pump(widget))
    except Exception:
        pass

    def _t():
        try:
            res = fn()
        except Exception as e:  # noqa: BLE001
            _UIQ.put(lambda: on_error(e))
        else:
            _UIQ.put(lambda: on_done(res))
    threading.Thread(target=_t, daemon=True).start()


def make_drop_listbox(parent, files_var_desc=""):
    """Buat Listbox + tombol tambah/hapus/naik/turun. Return (frame, listbox, files)."""
    import tkinter as tk
    from tkinter import filedialog, ttk

    files: list[str] = []
    frame = ttk.Frame(parent)
    try:
        from src.core import settings as _st
        _dark = _st.load().get("theme", "darkly") != "flatly"
    except Exception:
        try:
            from core import settings as _st  # noqa: F401
            _dark = _st.load().get("theme", "darkly") != "flatly"
        except Exception:
            _dark = True
    lb = tk.Listbox(frame, height=8, selectmode="extended", relief="flat",
                    font=("Segoe UI", 9),
                    bg="#1e1e1e" if _dark else "#ffffff",
                    fg="#d4d4d4" if _dark else "#212121",
                    selectbackground="#1f6feb", selectforeground="#ffffff",
                    highlightthickness=1)
    lb.pack(fill="both", expand=True)

    # drag-drop jika tkinterdnd2 tersedia
    try:
        from tkinterdnd2 import DND_FILES, TkinterDnD  # noqa
        lb.drop_target_register(DND_FILES)

        def _drop(ev):
            for p in parent.tk.splitlist(ev.data):
                p = p.strip("{}")
                if os.path.isfile(p) and p not in files:
                    files.append(p)
                    lb.insert("end", p)
        lb.dnd_bind("<<Drop>>", _drop)
    except Exception:
        pass

    bar = ttk.Frame(frame)
    bar.pack(fill="x", pady=4)

    def _add(pats):
        ps = filedialog.askopenfilenames(filetypes=pats)
        for p in ps:
            if p not in files:
                files.append(p)
                lb.insert("end", p)

    ttk.Button(bar, text="+ Tambah", command=lambda: _add(
        [("PDF & gambar", "*.pdf *.png *.jpg *.jpeg *.webp"), ("Semua", "*.*")])).pack(side="left")
    ttk.Button(bar, text="- Hapus", command=lambda: _del()).pack(side="left", padx=4)
    ttk.Button(bar, text="▲", width=3, command=lambda: _move(-1)).pack(side="right")
    ttk.Button(bar, text="▼", width=3, command=lambda: _move(1)).pack(side="right", padx=4)

    def _del():
        for i in reversed(lb.curselection()):
            lb.delete(i)
            del files[i]

    def _move(d):
        sel = list(lb.curselection())
        if not sel:
            return
        i = sel[0]
        j = i + d
        if 0 <= j < len(files):
            files[i], files[j] = files[j], files[i]
            lb.delete(0, "end")
            for p in files:
                lb.insert("end", p)
            lb.select_set(j)

    frame.files = files  # type: ignore[attr-defined]
    return frame, lb, files
