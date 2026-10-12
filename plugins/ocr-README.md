# Plugin OCR Portable (Tesseract)

Core (`src/core/ocr_ops.py`) memanggil `tesseract.exe` via subprocess —
tanpa pip tambahan. Agar portable, isi folder ini:

```
plugins/
  ocr-README.md        <- file ini
  tesseract/
    tesseract.exe      <- build portable Windows (64-bit)
    tessdata/
      ind.traineddata  <- ~1.5MB
      eng.traineddata  <- ~4MB
```

## Cara isi (Windows, sekali saja)

1. Unduh build portable: https://github.com/UB-Mannheim/tesseract/wiki
   pilih `tesseract-ocr-w64-setup` **portable .zip**, extract ke `plugins/tesseract/`
   sehingga ada `plugins/tesseract/tesseract.exe`.
2. Bahasa Indonesia: https://github.com/tesseract-ocr/tessdata_fast/raw/main/ind.traineddata
   simpan ke `plugins/tesseract/tessdata/ind.traineddata`.
   Inggris (`eng.traineddata`) biasanya sudah bawaan; bila tidak ada, unduh sama.
3. Buka menu OCR di app — badge harus berubah jadi `OCR ✓ siap`.

Tanpa folder ini app tetap jalan 12 tool lain; menu OCR menampilkan
instruksi ini dan menolak proses dengan pesan jelas (tidak crash).

## Ukuran

tesseract.exe ±8MB + tessdata ind+eng ±6MB → total plugin ±14MB.
Tetap di luar zip utama agar unduhan inti <30MB.

## Linux (dev)

`apt install tesseract-ocr tesseract-ocr-ind` lalu tesseract ada di PATH —
`ocr_ops.status()` otomatis pakai itu tanpa folder plugin.
