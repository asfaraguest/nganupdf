#!/usr/bin/env bash
# Build portable Windows/Linux: folder siap-zip, tanpa install.
# Windows: jalankan di PC target via `python -m PyInstaller ...` (perintah sama).
set -e
cd "$(dirname "$0")"
pip install --break-system-packages -q -r requirements.txt 2>/dev/null || pip install -q -r requirements.txt
python -m PyInstaller --noconfirm --clean \
  --name NganuPDF \
  --onedir --noconsole \
  --strip \
  --icon assets\icon.ico \
  --exclude-module numpy --exclude-module scipy --exclude-module pandas \
  --exclude-module matplotlib --exclude-module IPython --exclude-module tkinter.test \
  --collect-submodules pymupdf \
  --hidden-import PIL._tkinter_finder \
  --add-data "assets:assets" \
  src/main.py
echo "OK -> dist/NganuPDF/ (data/ dibuat otomatis saat jalan). Zip folder itu untuk portable."
