"""Office -> PDF via MS Office terinstall (Windows). Tanpa Office -> error jelas.

Tidak menambah dependensi wajib: comtypes diimpor lazy, hanya di Windows.
Tambahkan `comtypes; sys_platform=='win32'` ke requirements untuk memakainya.
"""
from __future__ import annotations

import os
import sys

OFFICE_EXTS = (".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt")


class OfficeError(RuntimeError):
    pass


def available() -> tuple[bool, str]:
    if sys.platform != "win32":
        return False, "Hanya di Windows + MS Office terinstall."
    try:
        import comtypes  # noqa: F401
    except ImportError:
        return False, "Butuh `pip install comtypes` + MS Office."
    return True, "siap"


def office_to_pdf(files: list[str], out_dir: str, progress=None) -> list[str]:
    ok, msg = available()
    if not ok:
        raise OfficeError(msg)
    import comtypes.client
    todo = [f for f in (files or []) if f.lower().endswith(OFFICE_EXTS)
            and os.path.isfile(f)]
    if not todo:
        raise ValueError("Pilih file Word/Excel/PowerPoint.")
    os.makedirs(out_dir, exist_ok=True)
    made: list[str] = []
    word = excel = ppt = None
    try:
        for i, fp in enumerate(todo):
            if progress:
                progress(i, len(todo))
            ext = os.path.splitext(fp)[1].lower()
            out = os.path.join(out_dir, os.path.splitext(os.path.basename(fp))[0] + ".pdf")
            if ext in (".docx", ".doc"):
                if word is None:
                    word = comtypes.client.CreateObject("Word.Application")
                    word.Visible = False
                doc = word.Documents.Open(os.path.abspath(fp))
                try:
                    doc.ExportAsFixedFormat(os.path.abspath(out), 17)  # wdExportFormatPDF
                finally:
                    doc.Close(False)
            elif ext in (".xlsx", ".xls"):
                if excel is None:
                    excel = comtypes.client.CreateObject("Excel.Application")
                    excel.Visible = False
                    excel.DisplayAlerts = False
                wb = excel.Workbooks.Open(os.path.abspath(fp))
                try:
                    wb.ExportAsFixedFormat(0, os.path.abspath(out))  # xlTypePDF
                finally:
                    wb.Close(False)
            else:
                if ppt is None:
                    ppt = comtypes.client.CreateObject("PowerPoint.Application")
                pres = ppt.Presentations.Open(os.path.abspath(fp), True, False, False)
                try:
                    pres.ExportAsFixedFormat(os.path.abspath(out), 2)  # ppFixedFormatTypePDF
                finally:
                    pres.Close()
            made.append(out)
        if progress:
            progress(len(todo), len(todo))
    finally:
        for app in (word, excel):
            try:
                if app is not None:
                    app.Quit()
            except Exception:
                pass
        try:
            if ppt is not None:
                ppt.Quit()
        except Exception:
            pass
    return made
