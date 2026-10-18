# Data Tugas 1

## Aturan Penyimpanan yang Diikuti

Repo tugas menetapkan tiga aturan soal folder `data/`:

1. Jangan commit dataset mentah atau hasil olahan berukuran besar ke Git.
2. File pada `data/raw/` adalah data asli dan tidak boleh diubah.
3. Simpan hasil transformasi yang dapat direproduksi pada `data/processed/`.

Isi folder ini disusun mengikuti ketiganya:

```text
data/
├── README.md
├── raw/
│   └── berita_politik/                     <- berkas asli, tidak pernah diubah
│       ├── train-00000-of-00022.parquet
│       └── ... (9 berkas, 1.716 MB)
└── processed/
    ├── .gitkeep
    └── berita_politik_640rb.parquet        <- tabel analisis, 542,4 MB
```

Yang masuk Git cuma `data/README.md` dan berkas `.gitkeep`. `.gitignore` sudah
menutup `data/raw/*` dan `data/processed/*`, jadi berkas besar tidak akan
ter-commit.

## Dataset yang Dipilih

| Item | Isi |
|---|---|
| Nama dataset | Indonesian Political News Clean |
| Isi | kumpulan berita politik dari portal berita Indonesia |
| Sumber | `https://huggingface.co/datasets/ardimardiana/indonesian-political-news-clean` |
| Revisi dipakai | `5da6267ea89cfba359a0d061738b22cc878dfe85` |
| Lisensi | Tidak dicantumkan oleh pengunggah. Dipakai untuk keperluan tugas kuliah dengan menyebut sumbernya. |
| Bentuk asli | 22 berkas Parquet, 1.628.288 baris, 15 kolom, 5.430 MB |
| Unit analisis | satu berita |

Halaman dataset bisa dibuka langsung di Hugging Face, termasuk penampil
datanya. Berkas Parquet-nya juga bisa diunduh manual dari tab Files tanpa
memakai skrip apa pun.

## Berkas Asli di data/raw

Yang diunduh 9 berkas pertama dari 22 berkas yang ada, totalnya 1.716 MB.
Berkasnya dibaca apa adanya, tidak ada satu nilai pun yang diubah. Berkas
ke-10 sampai ke-22 tidak ikut diunduh karena tabel analisisnya sudah cukup di
640.000 baris.

Jumlah baris tiap berkas seragam, 74.013 baris, jadi 9 berkas berisi 666.117
baris.

## Tabel Analisis di data/processed

`berita_politik_640rb.parquet` adalah hasil transformasi dari berkas asli:
barisnya dipotong di 640.000 dan kolomnya dipilih 10 dari 15.

| | |
|---|---|
| Baris | 640.000 |
| Kolom | 10 |
| Ukuran | 542,4 MB (542.417.137 byte) |
| SHA-256 | `dc308140abf503b526c43b55964a91d2b1c201efb9765ccb19dc9b33655ed2c5` |

Kenapa diambil sebagian: tugas meminta dataset minimal 500 MB atau lebih dari
1 juta baris, dan tidak lebih dari dua kali lipatnya. Bentuk aslinya 5.430 MB,
jauh di atas itu. Dengan dipotong di 640.000 baris, hasilnya 542,4 MB, jadi
masih di atas 500 MB tetapi hanya sekitar separuh dari batas dua kali lipat.
Urutan baris di dalam Parquet tetap, jadi tabel ini bisa dibuat ulang dan
hasilnya sama.

Batas 640.000 baris juga dipilih karena keterbatasan memori. Pada 1.200.000
baris berkasnya 968 MB dan notebook pembersihan kehabisan memori saat menyalin
tabel beberapa kali. Pada 640.000 baris proses yang sama berjalan tanpa
kendala.

### Kolom yang Dibuang

Dari 15 kolom, 5 dibuang supaya ukurannya turun. Yang paling besar
`news_raw_data`, isinya JSON mentah hasil pengambilan data termasuk seluruh isi
artikel dalam bentuk mentah. Teks bersihnya sudah ada di `news_text`, jadi
kolom itu murni duplikasi.

| Kolom dibuang | Porsi ukuran | Alasan |
|---|---|---|
| `news_raw_data` | 45,7% | JSON mentah, duplikat dari `news_text` |
| `news_guid` | 7,0% | penanda panjang, `id` sudah ada |
| `news_image` | 0,4% | alamat gambar, hampir semuanya kosong |
| `create_date` | 0,1% | tanggal internal basis data |
| `update_date` | 0,3% | tanggal internal basis data |

## Kolom pada Tabel Analisis

| Kolom | Isi | Contoh |
|---|---|---|
| `id` | penanda unik berita | `1924973` |
| `news_title` | judul berita | `Dana Kegiatan Isbat Nikah Bakal Diajukan di APBD Perubahan 2026` |
| `news_source` | alamat lengkap halaman berita | `https://radarutara.disway.id/...` |
| `news_author` | nama penulis | `Wahyudi` |
| `news_hostname` | nama domain portal | `disway.id` |
| `news_date` | waktu terbit, format `YYYY-MM-DD HH:MM:SS+00:00` | `2026-04-27 01:30:00+00:00` |
| `news_text` | isi lengkap berita | |
| `news_tags` | daftar kata kunci | `['apbd perubahan 2026', ...]` |
| `news_kabkot` | kabupaten atau kota yang dibahas | `Kabupaten Mukomuko` |
| `news_intent` | hasil analisis maksud berita, memuat daftar tempat | `{'intent': 'lapor_informasi', 'places': [...]}` |

## Cara Memperoleh Data

Ada dua jalan, pilih salah satu.

**Unduh manual lewat browser.** Buka halaman dataset di Hugging Face, masuk ke
tab Files, unduh berkas `train-00000-of-00022.parquet` sampai
`train-00008-of-00022.parquet`, lalu letakkan di `data/raw/berita_politik/`.
Setelah itu jalankan skrip dengan `--batas-baris 640000` untuk menyusun tabel
analisisnya. Cara ini tidak butuh koneksi skrip apa pun.

**Lewat skrip.** Jalankan dari root repo:

```bash
python src/download_dataset.py
```

Skrip mengerjakan dua hal: mengunduh berkas asli ke `data/raw/berita_politik/`
(1.716 MB, hanya sekali), lalu menyusun tabel analisis ke
`data/processed/berita_politik_640rb.parquet`.

Pilihan lain:

```bash
python src/download_dataset.py --batas-baris 20000   # uji cepat
python src/download_dataset.py --hapus-asli          # buang berkas asli setelah selesai
```

Satu hal yang perlu dicatat soal cara unduhnya. DuckDB bisa membaca Parquet
jarak jauh dan hanya mengambil kolom yang dipilih, tapi caranya memakai banyak
permintaan kecil. Diukur di jaringan ini hasilnya hanya 0,44 MB per detik.
Mengunduh berkas utuh secara paralel jauh lebih cepat, sekitar 7 MB per detik.
Karena itu berkas asli diunduh penuh lebih dulu, baru disusun tabelnya secara
lokal.

## Temuan Awal Sebelum Pembersihan

Angka di bawah ini hasil profiling di `notebooks/01_data_profiling.ipynb`,
bukan perkiraan.

| Temuan | Angka |
|---|---|
| Nilai kosong `news_author` | 31.931 baris (4,99%) |
| Nilai kosong `news_date` | 16.624 baris (2,60%) |
| Tanggal di luar 2015-2026 | 116 baris, ada yang bertahun 2265 |
| Isi berita di bawah 300 karakter | 24.555 baris |
| Isi berita di atas 50.000 karakter | 4 baris, terpanjang 457.008 karakter |
| Duplikat `id` dan `news_title` | tidak ada |
| Portal terbanyak | `rri.co.id` (48.456), `tribunnews.com` (27.289), `detik.com` (12.290) |
| Kota terbanyak | Kota Malang (5.881), Kota Medan (5.329), Kota Semarang (5.095) |
| Jumlah kabupaten/kota | 1.003 |
| Jumlah portal | 5.109 |

Kolom `news_date` berisi nilai yang bentuknya benar tapi isinya tidak masuk
akal, seperti tahun 2265. Nilai seperti itu tidak terbaca sebagai error saat
dibuka, jadi harus disaring pakai rentang tanggal yang wajar di tahap
pembersihan.
