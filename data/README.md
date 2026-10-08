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
│       └── ... (17 berkas, 3.989 MB)
└── processed/
    ├── .gitkeep
    └── berita_politik_1_2jt.parquet        <- tabel analisis, 968,4 MB
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

## Berkas Asli di data/raw

Yang diunduh 17 berkas pertama dari 22 berkas yang ada, totalnya 3.989 MB. Berkasnya
dibaca apa adanya, tidak ada satu nilai pun yang diubah. Berkas ke-18 sampai
ke-22 tidak ikut diunduh karena tabel analisisnya sudah cukup di 1.200.000
baris.

Jumlah baris tiap berkas seragam, 74.013 baris, jadi 17 berkas berisi
1.258.223 baris.

## Tabel Analisis di data/processed

`berita_politik_1_2jt.parquet` adalah hasil transformasi dari berkas asli:
barisnya dipotong di 1.200.000 dan kolomnya dipilih 10 dari 15.

| | |
|---|---|
| Baris | 1.200.000 |
| Kolom | 10 |
| Ukuran | 968,4 MB (968.411.112 byte) |
| SHA-256 | `0923acd744ea6fb2e68981aee6c54e84abc2181d6e2d84ce86cce34af2126c2f` |

Kenapa diambil sebagian: tugas meminta dataset minimal 500 MB atau lebih dari
1 juta baris, dan tidak lebih dari dua kali lipatnya. Bentuk aslinya 5.430 MB,
jauh di atas itu. Dengan dipotong di 1.200.000 baris, hasilnya masuk rentang
yang diminta dari dua sisi sekaligus, yaitu jumlah barisnya maupun ukurannya.
Urutan baris di dalam Parquet tetap, jadi tabel ini bisa dibuat ulang dan
hasilnya sama.

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

Jalankan skrip dari root repo:

```bash
python src/download_dataset.py
```

Skrip mengerjakan dua hal: mengunduh berkas asli ke `data/raw/berita_politik/`
(3.989 MB, hanya sekali), lalu menyusun tabel analisis ke
`data/processed/berita_politik_1_2jt.parquet`.

Pilihan lain:

```bash
python src/download_dataset.py --batas-baris 20000   # uji cepat
python src/download_dataset.py --hapus-asli          # buang berkas asli setelah selesai
```

Satu hal yang perlu dicatat soal cara unduhnya. DuckDB bisa membaca Parquet
jarak jauh dan hanya mengambil kolom yang dipilih, tapi caranya memakai banyak
permintaan kecil. Diukur di jaringan ini hasilnya hanya 0,44 MB per detik, jadi
seluruh 17 berkas butuh sekitar satu jam. Mengunduh berkas utuh secara paralel
jauh lebih cepat, sekitar 7 MB per detik. Karena itu berkas asli diunduh penuh
lebih dulu, baru disusun tabelnya secara lokal.

## Temuan Awal Sebelum Pembersihan

Angka di bawah ini hasil profiling di `notebooks/01_data_profiling.ipynb`,
bukan perkiraan.

| Temuan | Angka |
|---|---|
| Nilai kosong `news_author` | 94.607 baris (7,88%) |
| Nilai kosong `news_date` | 60.333 baris (5,03%) |
| Tanggal di luar 2015-2026 | 284 baris, ada yang bertahun 0001 dan 2285 |
| Isi berita di bawah 300 karakter | 67.557 baris (5,63%) |
| Isi berita di atas 50.000 karakter | 7 baris, terpanjang 1.062.327 karakter |
| Duplikat `id` dan `news_title` | tidak ada |
| Portal terbanyak | `tribunnews.com` (81.711), `rri.co.id` (72.748), `jawapos.com` (29.165) |
| Kota terbanyak | Kota Malang (11.924), Kota Bandung (11.211), Kota Medan (10.829) |

Kolom `news_date` berisi nilai yang bentuknya benar tapi isinya tidak masuk
akal, seperti tahun 0001 dan 2285. Nilai seperti itu tidak terbaca sebagai
error saat dibuka, jadi harus disaring pakai rentang tanggal yang wajar di
tahap pembersihan.
