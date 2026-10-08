"""Unduh dataset berita politik Indonesia, lalu susun tabel analisisnya.

Aturan penyimpanan yang diikuti
-------------------------------
Repo tugas menetapkan tiga aturan soal folder `data/`:

1. Jangan commit dataset mentah atau hasil olahan berukuran besar ke Git.
2. File pada `data/raw/` adalah data asli dan tidak boleh diubah.
3. Simpan hasil transformasi yang dapat direproduksi pada `data/processed/`.

Skrip ini mengikuti ketiganya:

- `data/raw/berita_politik/` hanya berisi berkas Parquet asli hasil unduhan.
  Isinya tidak pernah disentuh, dibaca apa adanya.
- `data/processed/berita_politik_1_2jt.parquet` berisi tabel hasil susunan,
  yaitu pemotongan baris dan pemilihan kolom. Ini hasil transformasi, jadi
  tempatnya di `data/processed/`.
- Keduanya tidak di-commit. `.gitignore` sudah menutup `data/raw/*` dan
  `data/processed/*`, yang masuk Git cuma `data/README.md`.

Sumber data
-----------
Kumpulan berita politik dari portal berita Indonesia, dipublikasikan di
Hugging Face sebagai:

    https://huggingface.co/datasets/ardimardiana/indonesian-political-news-clean

Bentuk aslinya sudah rapi: 22 berkas Parquet, 1.628.288 baris, 15 kolom,
totalnya 5,4 GB. Tiap berkas berisi 74.013 baris.

Kenapa diambil sebagian
-----------------------
Tugas meminta dataset minimal 500 MB atau lebih dari 1 juta baris, dan tidak
lebih dari dua kali lipatnya. Bentuk aslinya 5,4 GB, jauh di atas itu.

Yang diambil 1.200.000 baris pertama mengikuti urutan berkas. Jumlah itu masih
di atas 1 juta baris tetapi tidak sampai 2 juta, dan berkas hasilnya 968 MB.
Jadi rentang yang diminta terpenuhi dari dua sisi. Urutan baris di dalam
Parquet tetap, jadi hasilnya sama setiap kali dijalankan.

Kolom yang dibuang
------------------
Dari 15 kolom, 5 dibuang. Yang paling besar `news_raw_data` (45,7% dari total
ukuran), isinya JSON mentah hasil pengambilan data termasuk seluruh isi artikel
dalam bentuk mentah. Teks bersihnya sudah ada di `news_text`, jadi kolom itu
murni duplikasi.

| Kolom dibuang | Porsi ukuran | Alasan |
|---|---|---|
| `news_raw_data` | 45,7% | JSON mentah, duplikat dari `news_text` |
| `news_guid` | 7,0% | penanda panjang, `id` sudah ada |
| `news_image` | 0,4% | alamat gambar, hampir semuanya kosong |
| `create_date` | 0,1% | tanggal internal basis data |
| `update_date` | 0,3% | tanggal internal basis data |

Kenapa diunduh berkas utuh lebih dulu
-------------------------------------
DuckDB bisa membaca Parquet jarak jauh dan hanya mengambil kolom yang dipilih,
tapi caranya memakai banyak permintaan kecil. Diukur di jaringan ini hasilnya
0,44 MB per detik. Unduh berkas utuh secara paralel jauh lebih cepat, sekitar
7 MB per detik. Jadi berkas asli diunduh penuh lebih dulu, baru dipotong dan
dipilih kolomnya secara lokal.

Pemakaian:
    python src/download_dataset.py
    python src/download_dataset.py --batas-baris 20000   (uji cepat)
    python src/download_dataset.py --hapus-asli          (buang berkas asli)
"""

from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import duckdb
import requests

# Revisi dikunci supaya isi dataset tidak berubah sewaktu-waktu.
REVISI = "5da6267ea89cfba359a0d061738b22cc878dfe85"

AKAR_REPO = Path(__file__).resolve().parent.parent

# Berkas asli hasil unduhan. Isinya tidak boleh diubah.
RAW = AKAR_REPO / "data" / "raw" / "berita_politik"

# Tabel hasil susunan. Ini hasil transformasi, jadi masuk data/processed/.
OUTPUT = AKAR_REPO / "data" / "processed" / "berita_politik_1_2jt.parquet"
TEMP = OUTPUT.with_suffix(".parquet.part")

AKAR_BERKAS = (
    "https://huggingface.co/datasets/ardimardiana/indonesian-political-news-clean"
    f"/resolve/{REVISI}/data"
)

# 17 berkas pertama berisi 1.258.223 baris. Dipakai 1.200.000 di antaranya.
JUMLAH_BERKAS = 17
BATAS_BARIS = 1_200_000
UTAS = 6
MAKS_PERCOBAAN = 3

# Kolom yang dipakai, urut sesuai berkas aslinya.
KOLOM = [
    "id",
    "news_title",
    "news_source",
    "news_author",
    "news_hostname",
    "news_date",
    "news_text",
    "news_tags",
    "news_kabkot",
    "news_intent",
]


def daftar_berkas() -> list[str]:
    return [f"train-{i:05d}-of-00022.parquet" for i in range(JUMLAH_BERKAS)]


def unduh_berkas(sesi: requests.Session, nama: str) -> Path:
    """Unduh satu berkas asli ke data/raw. Kalau sudah ada, langsung dipakai."""
    tujuan = RAW / nama
    if tujuan.exists() and tujuan.stat().st_size > 1_000_000:
        return tujuan

    for percobaan in range(1, MAKS_PERCOBAAN + 1):
        try:
            resp = sesi.get(f"{AKAR_BERKAS}/{nama}", timeout=600)
            resp.raise_for_status()
            # Ditulis ke berkas sementara dulu supaya tidak menyimpan berkas
            # yang terpotong.
            sementara = tujuan.with_suffix(".part")
            sementara.write_bytes(resp.content)
            sementara.replace(tujuan)
            return tujuan
        except Exception:
            if percobaan == MAKS_PERCOBAAN:
                raise
    return tujuan


def susun(batas_baris: int) -> None:
    """Bentuk tabel analisis dari berkas asli, tanpa mengubah berkas aslinya."""
    con = duckdb.connect()
    con.execute("SET enable_progress_bar = false")
    con.execute("SET threads = 4")
    con.execute("SET memory_limit = '4GB'")
    # Urutan baris dijaga supaya hasilnya sama setiap kali dijalankan.
    con.execute("SET preserve_insertion_order = true")

    daftar = ", ".join(f"'{(RAW / n).as_posix()}'" for n in daftar_berkas())
    kolom = ", ".join(KOLOM)

    con.execute(
        f"""
        COPY (
            SELECT {kolom}
            FROM read_parquet([{daftar}])
            LIMIT {batas_baris}
        ) TO '{TEMP.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """
    )


def periksa(path: Path) -> int:
    """Kembalikan jumlah baris, atau 0 kalau berkasnya belum utuh."""
    if not path.exists():
        return 0
    with open(path, "rb") as f:
        f.seek(-4, 2)
        if f.read(4) != b"PAR1":
            return 0
    try:
        con = duckdb.connect()
        con.execute("SET enable_progress_bar = false")
        hasil = con.execute(
            f"SELECT count(*) FROM read_parquet('{path.as_posix()}')"
        ).fetchone()
        return int(hasil[0]) if hasil else 0
    except Exception:
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--batas-baris",
        type=int,
        default=BATAS_BARIS,
        help=f"jumlah baris yang diambil (bawaan {BATAS_BARIS:,})",
    )
    parser.add_argument(
        "--hapus-asli",
        action="store_true",
        help="hapus berkas asli di data/raw/berita_politik setelah selesai",
    )
    opsi = parser.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    print(f"Mengunduh {JUMLAH_BERKAS} berkas asli ke data/raw/berita_politik ...")
    sesi = requests.Session()
    sesi.headers.update({"User-Agent": "tugas1-bigdata/1.0"})
    gagal: list[str] = []
    selesai = 0
    with ThreadPoolExecutor(UTAS) as kolam:
        tugas = {kolam.submit(unduh_berkas, sesi, n): n for n in daftar_berkas()}
        for tugas_selesai in tugas:
            nama = tugas[tugas_selesai]
            try:
                tugas_selesai.result()
            except Exception as e:
                gagal.append(nama)
                print(f"  gagal: {nama} ({type(e).__name__})")
            selesai += 1
            if selesai % 5 == 0:
                print(f"  {selesai}/{JUMLAH_BERKAS}")

    if gagal:
        print(f"{len(gagal)} berkas gagal, jalankan ulang untuk mencoba lagi")

    ukuran_raw = sum(f.stat().st_size for f in RAW.glob("*.parquet"))
    print(f"  berkas asli: {ukuran_raw / 1e6:,.0f} MB")

    print(
        f"Menyusun {opsi.batas_baris:,} baris dengan {len(KOLOM)} kolom "
        "ke data/processed ..."
    )
    susun(opsi.batas_baris)

    baris = periksa(TEMP)
    if baris == 0:
        print("Berkas hasil tidak valid.")
        return 1
    TEMP.replace(OUTPUT)

    if opsi.hapus_asli:
        for f in RAW.glob("*"):
            f.unlink()
        RAW.rmdir()
        print("Berkas asli dihapus. Jalankan ulang skrip ini untuk mengunduhnya lagi.")

    ukuran = OUTPUT.stat().st_size / 1e6
    print()
    print(f"Berkas asli  : data/raw/berita_politik/ ({JUMLAH_BERKAS} berkas)")
    print(f"Tabel analisis: data/processed/{OUTPUT.name}")
    print(f"Baris        : {baris:,}")
    print(f"Kolom        : {len(KOLOM)}")
    print(f"Ukuran       : {ukuran:,.1f} MB")
    print(
        f"Syarat tugas : "
        f"{'terpenuhi' if baris > 1_000_000 else 'BELUM'} (>1.000.000 baris)"
    )
    return 0 if baris > 1_000_000 else 1


if __name__ == "__main__":
    sys.exit(main())
