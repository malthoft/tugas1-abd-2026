"""Pemuatan dataset untuk notebook Tugas 1.

FineWeb-2 versi Indonesia dipakai sebagai dataset utama. File di data/raw/
berisi 1,2 juta dokumen hasil pemotongan shard pertama, lihat
src/download_dataset.py dan data/README.md.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

# Path dihitung dari lokasi berkas ini, bukan dari folder kerja, supaya modul
# tetap benar walau diimpor dari dalam folder notebooks/.
AKAR_REPO = Path(__file__).resolve().parent.parent

DATA_RAW = AKAR_REPO / "data" / "raw" / "fineweb2_indo_1_2jt.parquet"
DATA_BERSIH = AKAR_REPO / "data" / "processed" / "fineweb2_indo_bersih.parquet"

# Kolom tanggal pada FineWeb-2 berisi waktu crawl (format YYYY-MM-DDTHH:MM:SSZ)
KOLOM_TANGGAL = "date"
KOLOM_TEKS = "text"


def data_mentah(path: str | Path = DATA_RAW) -> pl.LazyFrame:
    """Dataset mentah sebagai LazyFrame supaya pemrosesan hemat memori."""
    return pl.scan_parquet(path)


def data_bersih(path: str | Path = DATA_BERSIH) -> pl.LazyFrame:
    """Hasil pembersihan dari notebook 02."""
    return pl.scan_parquet(path)


def domain_dari_url(kolom: str = "url") -> pl.Expr:
    """Ambil nama domain dari kolom url (hapus www. dan path)."""
    return (
        pl.col(kolom)
        .str.replace(r"^https?://", "")
        .str.split("/")
        .list.first()
        .str.replace(r"^www\.", "")
        .alias("domain")
    )
