# PDFTool Portable — multitool PDF offline ala PDF24

Techstack minimal: **Python + PyMuPDF + Pillow + tkinter + ttkbootstrap + tkinterdnd2**.
Tanpa Node, tanpa Rust, tanpa server. 100% offline.

## Jalankan (Windows)

1. Install Python 3.12 + centang `tcl/tk`.
2. `pip install -r requirements.txt`
3. `py src/main.py` — atau dobel-klik `PDFTool.exe` hasil build.

## Build .exe portable (di PC Windows)

Klik 2x `build-windows.bat`, hasil: `dist\PDFTool\PDFTool.exe` + ikon.
Folder `dist\PDFTool` + `data\` + `plugins\` = paket portable siap-zip.
Tips kecilkan hasil: di Windows UPX aktif default bila `upx.exe` ada di PATH.

## Cross-build .exe dari Linux (terbukti jalan, 2026-10-12)

PyInstaller tidak cross-compile, jadi dipakai **Wine 11 + Python Windows**:
`dist-win/PDFTool-v1.0-win64-portable.zip` (39MB) di-build di server ini via
Kron4ek Wine portable + `python-3.12.10-amd64.exe /quiet` + PyInstaller
`--onedir --noconsole`. Smoke-test + screenshot dashboard OK di bawah
`xvfb`+Wine. Ulangi: pasang Wine 64-bit → install Python Windows + pip deps
→ copy proyek ke `C:\pdf-tool` → jalankan perintah yang sama seperti
`build-windows.bat` via `wine cmd /c`.

## Build Linux (terbukti jalan di sini)

`source dev-env.sh` (tkinter tanpa sudo, khusus server ini) lalu
`bash build-portable.sh`. Hasil terverifikasi 2026-10-10:
`dist/PDFTool` 102MB → zip 72MB, smoke-test GUI + screenshot dashboard OK
di bawah `xvfb`. Catatan: PyInstaller menonaktifkan UPX di Linux
(inkompatibilitas .so); di Windows UPX tetap bisa dipakai.

Di Linux server ini `tkinter` sistem tidak ada (tanpa sudo), jadi GUI hanya jalan
di Windows/PC desktop. Core sudah dites headless: `python3 tests/test_core.py`.

## Fitur P0+P1+P2 (13 tool, dashboard grid)

Merge (+preview thumbnail), Split (+preview strip), Rotate, Hapus/Extract,
Compress, Img→PDF, PDF→Img, Watermark, Nomor halaman, Metadata,
Protect, Unlock, **OCR → PDF searchable (plugin opsional)**.

## Portable

- `build-portable.sh` → `dist/PDFTool/` → zip → colok USB.
- Settings di `data/settings.json` sebelah exe (bukan %APPDATA%).
- OCR: isi `plugins/tesseract/` + `tessdata ind+eng` sesuai `plugins/ocr-README.md`
  (±14MB). Tanpa itu 12 tool lain tetap jalan; badge dashboard `OCR ✗/✓`.
- Office-convert sengaja tidak dibundel
  agar zip tetap <30MB. Tambahkan manual bila perlu.

## Ukuran (aktual, bukan estimasi)

Linux `--onedir --strip`: folder 102MB (terbesar: PyMuPDF 53MB + Pillow 14MB
+ Python 9MB), zip 72MB. Windows kurang-lebih sama, bisa susut dengan UPX.
`--onefile` tidak dipakai (start lambat).
