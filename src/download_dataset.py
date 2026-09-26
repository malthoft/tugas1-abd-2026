"""Unduh subset dataset FineWeb-2 (config ind_Latn) ke folder data/raw.

Dataset aslinya 152 GB (32 file Parquet, sekitar 100 juta dokumen), shard
pertamanya saja 4,8 GB, jadi terlalu berat untuk dikerjakan di laptop ini.
Skrip ini mengambil 1.200.000 dokumen pertama dari shard pertama. Urutan baris
di dalam file Parquet tidak berubah, jadi hasilnya tetap sama setiap kali
dijalankan dan tidak ada sampling acak.

Jumlah baris tersebut sudah memenuhi syarat tugas (lebih dari 1 juta baris).

Pemakaian:
    python src/download_dataset.py
"""

from __future__ import annotations

import os
import sys

import duckdb

BASE = "https://huggingface.co/datasets/HuggingFaceFW/fineweb-2/resolve/main"
SHARD = f"{BASE}/data/ind_Latn/train/000_00000.parquet"
OUTPUT = "data/raw/fineweb2_indo_1_2jt.parquet"
JUMLAH_BARIS = 1_200_000
MAKS_PERCOBAAN = 3

# Unduhan lewat jaringan pernah terputus di tengah jalan dan menyisakan file
# Parquet tanpa footer, jadi setiap percobaan ditulis ke file sementara dulu
# dan baru diverifikasi setelah selesai.
TEMP = OUTPUT + ".part"


def unduh() -> None:
    con = duckdb.connect()
    con.execute("INSTALL httpfs")
    con.execute("LOAD httpfs")
    # Jaringan ke Hugging Face pernah memutus koneksi di tengah pembacaan,
    # jadi jumlah percobaan ulang HTTP dinaikkan dari bawaan 3.
    con.execute("SET http_retries = 20")
    con.execute("SET http_timeout = 300000")
    con.execute(
        f"""
        COPY (
            SELECT * FROM read_parquet('{SHARD}')
            LIMIT {JUMLAH_BARIS}
        ) TO '{TEMP}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """
    )


def file_utuh(path: str) -> tuple[bool, int]:
    """True kalau footer Parquet masih ada dan jumlah barisnya cukup."""
    if not os.path.exists(path):
        return False, 0
    with open(path, "rb") as f:
        f.seek(-4, os.SEEK_END)
        if f.read(4) != b"PAR1":
            return False, 0
    try:
        con = duckdb.connect()
        baca = con.execute(f"SELECT count(*) FROM read_parquet('{path}')").fetchone()
        baris = int(baca[0]) if baca else 0
    except Exception:
        return False, 0
    return baris >= 1_000_000, baris


def main() -> int:
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

    if file_utuh(OUTPUT)[0]:
        print(f"File sudah lengkap, unduhan dilewati: {OUTPUT}")
    else:
        for percobaan in range(1, MAKS_PERCOBAAN + 1):
            print(f"Percobaan {percobaan}/{MAKS_PERCOBAAN}: mengambil {JUMLAH_BARIS:,} baris dari shard ind_Latn...")
            try:
                unduh()
            except Exception as e:
                print(f"  gagal: {type(e).__name__}: {e}")

            ok, baris = file_utuh(TEMP)
            if ok:
                os.replace(TEMP, OUTPUT)
                print(f"  selesai: {baris:,} baris")
                break
            print(f"  file belum valid ({baris:,} baris), diulang")
            if os.path.exists(TEMP):
                os.remove(TEMP)
        else:
            print("Unduhan gagal setelah semua percobaan.")
            return 1

    baris = file_utuh(OUTPUT)[1]
    ukuran = os.path.getsize(OUTPUT) / 1e6
    print(f"File    : {OUTPUT}")
    print(f"Baris   : {baris:,}")
    print(f"Ukuran  : {ukuran:,.1f} MB")
    return 0 if baris >= 1_000_000 else 1


if __name__ == "__main__":
    sys.exit(main())
