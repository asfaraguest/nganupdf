"""Widget reusable: DropZone (drag-drop), FileList, run_async worker."""
import os
import threading


def run_async(fn, on_done, on_error):
    """Jalankan fn() di thread agar UI tidak freeze."""
    def _t():
        try:
            res = fn()
        except Exception as e:  # noqa: BLE001
            on_error(e)
        else:
            on_done(res)
    threading.Thread(target=_t, daemon=True).start()


def make_drop_listbox(parent, files_var_desc=""):
    """Buat Listbox + tombol tambah/hapus/naik/turun. Return (frame, listbox, files)."""
    import tkinter as tk
    from tkinter import filedialog, ttk

    files: list[str] = []
    frame = ttk.Frame(parent)
    lb = tk.Listbox(frame, height=8, selectmode="extended")
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
