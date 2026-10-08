"""Pemuatan dataset untuk notebook Tugas 1.

Ada dua lapis berkas, mengikuti aturan penyimpanan tugas:

- `data/raw/berita_politik/` berisi berkas Parquet asli dari Hugging Face,
  belum disentuh apa pun.
- `data/processed/berita_politik_1_2jt.parquet` berisi tabel hasil susunan
  `src/download_dataset.py`, yaitu 1.200.000 baris dengan 10 kolom. Tabel ini
  yang dipakai notebook, karena ukuran dan jumlah barisnya sudah masuk rentang
  yang diminta tugas.

Rincian sumber dan arti kolomnya ada di data/README.md.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

# Path dihitung dari lokasi berkas ini, bukan dari folder kerja, supaya modul
# tetap benar walau diimpor dari dalam folder notebooks/.
AKAR_REPO = Path(__file__).resolve().parent.parent

# Berkas asli, tidak pernah diubah isinya.
DATA_ASLI = AKAR_REPO / "data" / "raw" / "berita_politik"

# Tabel hasil susunan yang dipakai untuk analisis.
DATA_ANALISIS = AKAR_REPO / "data" / "processed" / "berita_politik_1_2jt.parquet"

# Hasil pembersihan dari notebook 02.
DATA_BERSIH = AKAR_REPO / "data" / "processed" / "berita_politik_bersih.parquet"

KOLOM_WAKTU = "news_date"
KOLOM_WILAYAH = "news_kabkot"
KOLOM_TEKS = "news_text"

# Kolom di tabel analisis beserta isinya.
KOLOM = {
    "id": "penanda unik berita",
    "news_title": "judul berita",
    "news_source": "alamat lengkap halaman berita",
    "news_author": "nama penulis",
    "news_hostname": "nama domain portal, mis. disway.id",
    "news_date": "waktu terbit",
    "news_text": "isi lengkap berita",
    "news_tags": "daftar kata kunci berita",
    "news_kabkot": "kabupaten atau kota yang dibahas",
    "news_intent": "hasil analisis maksud berita, memuat daftar tempat",
}


def data_analisis(path: str | Path = DATA_ANALISIS) -> pl.LazyFrame:
    """Tabel hasil susunan sebagai LazyFrame, dipakai notebook.

    Lazy berarti isi berkas belum dimuat ke memori sampai ada perintah yang
    benar-benar butuh hasilnya.
    """
    return pl.scan_parquet(path)


def data_asli(akar: str | Path = DATA_ASLI) -> pl.LazyFrame:
    """Seluruh berkas Parquet asli sekaligus, dibaca sebagai satu tabel.

    Dipakai kalau perlu membandingkan hasil susunan dengan sumber aslinya.
    """
    return pl.scan_parquet(Path(akar) / "*.parquet")


def data_bersih(path: str | Path = DATA_BERSIH) -> pl.LazyFrame:
    """Hasil pembersihan dari notebook 02."""
    return pl.scan_parquet(path)


def waktu_terbit(kolom: str = KOLOM_WAKTU) -> pl.Expr:
    """Kolom waktu terbit diubah dari teks ke datetime.

    Nilai aslinya berbentuk `2026-04-27 01:30:00+00:00`. `strict=False` dipakai
    supaya baris yang formatnya menyimpang jadi null, bukan menggagalkan
    seluruh pemrosesan.
    """
    return pl.col(kolom).str.to_datetime(strict=False, time_zone="UTC")


def panjang_teks(kolom: str = KOLOM_TEKS) -> pl.Expr:
    """Jumlah karakter isi berita."""
    return pl.col(kolom).str.len_chars().alias("panjang_teks")


def panjang_judul(kolom: str = "news_title") -> pl.Expr:
    """Jumlah karakter judul berita."""
    return pl.col(kolom).str.len_chars().alias("panjang_judul")


def domain(kolom: str = "news_hostname") -> pl.Expr:
    """Nama domain portal berita, huruf kecil dan tanpa awalan www."""
    return pl.col(kolom).str.to_lowercase().str.replace(r"^www\.", "").alias("domain")
