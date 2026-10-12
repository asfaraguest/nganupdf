@echo off
REM Build NganuPDF di Windows (jalankan dari folder proyek).
REM Butuh: Python 3.12 (centang tcl/tk) + pip.
setlocal
cd /d %~dp0

py -m pip install --upgrade pip
py -m pip install -r requirements.txt pyinstaller

py -m PyInstaller --noconfirm --clean ^
  --name NganuPDF ^
  --onedir --noconsole ^
  --icon assets\icon.ico ^
  --exclude-module numpy --exclude-module scipy --exclude-module pandas ^
  --exclude-module matplotlib --exclude-module IPython --exclude-module tkinter.test ^
  --collect-submodules pymupdf ^
  --hidden-import PIL._tkinter_finder ^
  --add-data assets;assets ^
  src\main.py

echo.
echo SELESAI: dist\NganuPDF\NganuPDF.exe
echo Copy folder dist\NganuPDF + data + plugins ke USB, lalu zip bila perlu.
echo Isi plugins\tesseract\ sesuai plugins\ocr-README.md untuk aktifkan OCR.
pause
