# Data Tugas 1

## Dataset yang Dipilih

| Item | Isi |
|---|---|
| Nama dataset | FineWeb-2, konfigurasi `ind_Latn` (korpus web berbahasa Indonesia) |
| Sumber | `https://huggingface.co/datasets/HuggingFaceFW/fineweb-2` |
| Lisensi/ketentuan pakai | ODC-By 1.0, boleh dipakai ulang dengan atribusi ke pembuat dataset |
| Ukuran | 1.200.000 baris, file di `data/raw/` berukuran 1,68 GB (1.681.446.412 byte) |
| Periode data | 2013 sampai 2024, mengikuti tanggal crawl Common Crawl pada kolom `date` |
| Unit analisis | satu dokumen web berbahasa Indonesia |

## Kenapa Bukan Seluruh Dataset

Shard pertama (`data/ind_Latn/train/000_00000.parquet`) saja berukuran 4,85 GB
(4.845.913.669 byte) dan berisi 3.149.000 baris. Keseluruhan konfigurasi
`ind_Latn` terdiri dari 32 file Parquet dengan total 152,15 GB, atau sekitar 99
juta dokumen. Laptop yang dipakai punya RAM 16 GB dan sisa ruang disk di bawah
20 GB, jadi yang diambil adalah potongan berurutan dari awal shard pertama,
bukan sampling acak:

- 1.200.000 dokumen pertama dari `data/ind_Latn/train/000_00000.parquet`
- urutan baris di dalam file Parquet tidak berubah, jadi unduhan bisa diulang
  dan menghasilkan file yang sama
- jumlah barisnya masih melewati syarat tugas, yaitu di atas 1 juta baris

## Cara Memperoleh Data

1. Jalankan skrip pengunduh dari root repo:

```bash
python src/download_dataset.py
```

Skrip memakai DuckDB dengan ekstensi `httpfs` untuk membaca shard jarak jauh,
mengambil 1.200.000 baris pertama, lalu menulisnya ke
`data/raw/fineweb2_indo_1_2jt.parquet` dengan kompresi ZSTD. Jumlah percobaan
ulang HTTP dinaikkan karena koneksi ke Hugging Face pernah terputus di tengah
pembacaan.

2. Skrip menulis ke file sementara `*.parquet.part` lebih dulu. File dipindahkan
   ke nama akhir hanya kalau footer Parquet lengkap dan jumlah barisnya sudah
   melewati 1 juta baris. Kalau unduhan terputus, jalankan ulang perintah yang sama.

3. Verifikasi hasilnya:

```bash
python -c "import duckdb; print(duckdb.sql(\"select count(*) from read_parquet('data/raw/fineweb2_indo_1_2jt.parquet')\").fetchone())"
```

## Checksum

| File | Ukuran (byte) | SHA-256 |
|---|---|---|
| `data/raw/fineweb2_indo_1_2jt.parquet` | 1.681.446.412 | `70ac59b299b88aabf87c6d4da10e9bef50693d9485f23daa5215d89ab4ddd617` |

Checksum dihitung dari file hasil unduhan, bukan dari dataset aslinya, karena yang
dipakai di tugas ini memang potongan shard tersebut.

## Kolom pada Dataset

| Kolom | Isi |
|---|---|
| `text` | isi teks halaman web |
| `id` | penanda dokumen (`urn:uuid:...`) |
| `dump` | batch crawl Common Crawl asal dokumen, mis. `CC-MAIN-2024-10` |
| `url` | URL halaman sumber |
| `date` | tanggal dan jam crawl, contoh `2013-05-19T22:07:28Z` |
| `file_path` | lokasi berkas asal di penyimpanan Common Crawl |
| `language` | label bahasa hasil deteksi, untuk dataset ini `ind` |
| `language_score` | skor keyakinan deteksi bahasa, 0 sampai 1 |
| `language_script` | jenis aksara, untuk dataset ini `Latn` |
| `minhash_cluster_size` | jumlah dokumen dalam klaster MinHash yang sama, petunjuk adanya duplikat |
| `top_langs` | daftar bahasa lain yang terdeteksi pada dokumen yang sama |

## Aturan Penyimpanan

- Dataset mentah tidak di-commit ke Git, hanya instruksi unduh di berkas ini.
- File di `data/raw/` tidak diubah isinya.
- Hasil transformasi disimpan di `data/processed/` dan bisa dibuat ulang dengan
  menjalankan notebook secara berurutan.
