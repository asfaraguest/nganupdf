@echo off
REM Build NganuPDF di Windows (jalankan dari folder proyek).
REM Butuh: Python 3.12 (centang tcl/tk) + pip.
setlocal
cd /d %~dp0

py -m pip install --upgrade pip
py -m pip install -r requirements.txt pyinstaller

for /f "delims=" %%i in ('py -c "import site;print(site.getsitepackages()[-1])"') do set "SP=%%i"

py -m PyInstaller --noconfirm --clean ^
  --name NganuPDF ^
  --onedir --noconsole ^
  --icon assets\icon.ico ^
  --exclude-module numpy --exclude-module scipy --exclude-module pandas ^
  --exclude-module matplotlib --exclude-module IPython --exclude-module tkinter.test ^
  --collect-submodules pymupdf ^
  --collect-submodules docx ^
  --collect-submodules pptx ^
  --collect-submodules openpyxl ^
  --hidden-import PIL._tkinter_finder ^
  --add-data assets;assets ^
  --add-binary "%SP%\msvcp140.dll;." ^
  --add-binary "%SP%\msvcp140_1.dll;." ^
  --add-binary "%SP%\msvcp140_2.dll;." ^
  --add-binary "%SP%\msvcp140_atomic_wait.dll;." ^
  --add-binary "%SP%\msvcp140_codecvt_ids.dll;." ^
  --add-binary "%SP%\vcruntime140_threads.dll;." ^
  src\main.py

echo.
echo SELESAI: dist\NganuPDF\NganuPDF.exe
echo Copy folder dist\NganuPDF + data + plugins ke USB, lalu zip bila perlu.
echo Isi plugins\tesseract\ sesuai plugins\ocr-README.md untuk aktifkan OCR.
pause
