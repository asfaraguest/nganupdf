# NganuPDF

Multitool PDF offline ala PDF24. Python + tkinter + PyMuPDF.
Tanpa install, tanpa internet.

## Fitur (30 tool, cari + filter kategori di sidebar)

Susun: Merge, Split, Atur Halaman (drag-drop antar-file), Hapus/Extract.
Edit: Rotate, Crop, Watermark, Teks, Nomor, Metadata, Redact, Sign, Form
(isi/daftar kolom AcroForm).
Konversi: Compress, Gambar→PDF, Scan→PDF, PDF→Gambar, Ambil Gambar
(ekstrak gambar tertanam), HTML→PDF, PDF→Markdown, Office→PDF (via
MS Office), OCR (plugin), PDF→Word (.docx), PDF→PowerPoint (.pptx),
PDF→Excel (.xlsx), PDF→PDF/A (via Ghostscript bila ada).
Keamanan: Protect, Unlock. Perbaiki: Repair PDF rusak, Banding
(bandingkan 2 PDF berdampingan + sorot beda).

Semua ala iLovePDF tapi 100% lokal: PDF→Word/PPT/Excel pakai python-docx,
python-pptx, openpyxl (tanpa internet); PDF/A pakai Ghostscript bila
tersedia, jika tidak hasil best-effort.

## Pakai (Windows)

1. Unduh zip dari [Releases](https://github.com/asfaraguest/nganupdf/releases), extract.
2. Dobel-klik `NganuPDF.exe`.

Setting tersimpan di folder `data\` sebelah exe. Untuk OCR,
lihat `plugins/ocr-README.md`.

## Jalan dari source

Butuh Python 3.12 (centang `tcl/tk` saat install).

```sh
pip install -r requirements.txt
py src/main.py        # Windows
bash run.sh           # Linux
```

## Build

```sh
build-windows.bat     # di Windows -> dist\NganuPDF
bash build-portable.sh  # di Linux  -> dist/NganuPDF
```

## Ukuran & privasi

Folder hasil build ±100MB (terbesar PyMuPDF + lxml), zip ±46MB.
100% offline: tidak ada kode jaringan di `src/`, tanpa telemetri,
tanpa update otomatis, tanpa upload file ke mana pun.
