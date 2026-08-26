"""
Traceability Service — Orkestrasi pembuatan & sinkronisasi block blockchain.

MASALAH YANG DIPERBAIKI DI FILE INI:
Pada versi sebelumnya, block blockchain hanya dibuat SEKALI saat batch dibuat
(jumlah_grade_a/b/c/reject masih 0 di titik itu). Setelah petani melakukan
scan/grading, kolom rekap di tabel batch_panen ter-update, TAPI block_data
dan block_hash di traceability_blockchain TIDAK PERNAH di-refresh.

Akibatnya: hash yang tersimpan tidak pernah mencerminkan data batch yang
sebenarnya, sehingga fitur "verifikasi integritas data" jadi tidak berguna
(hash awal vs data batch final pasti selalu terlihat "berbeda", padahal itu
bukan tanda manipulasi, itu memang belum pernah disinkronkan).

Fungsi `sync_block()` di bawah ini dipanggil ulang setiap ada perubahan data
batch (setelah grading baru masuk, atau saat status distribusi berubah).
Karena skema DB membatasi satu block per batch (kolom batch_id UNIQUE),
block yang sudah ada di-refresh (block_data & block_hash dihitung ulang),
bukan menambah block baru. previous_hash & block_index tetap dari saat
pertama kali dibuat, jadi urutan chain global tetap terjaga.
"""

from sqlalchemy.orm import Session

from app.models.batch import BatchPanen
from app.models.blockchain import TraceabilityBlockchain, GENESIS_HASH
from app.models.kebun import Kebun
from app.models.user import User
from app.services.blockchain_hash import build_block_data, compute_hash


def sync_block(db: Session, batch: BatchPanen) -> TraceabilityBlockchain:
    """
    Buat block baru (jika belum ada) atau refresh block yang sudah ada
    dengan data batch terbaru (total_buah, jumlah per grade, dst).

    Dipanggil dari:
    - batch_router.create_batch()        -> membuat block pertama kali
    - yolo_router.scan_pineapple()       -> refresh setelah ada grading baru
    - batch_router.update_batch_status() -> refresh saat status berubah
    """
    kebun = db.query(Kebun).filter(Kebun.id == batch.kebun_id).first()
    petani = db.query(User).filter(User.id == kebun.petani_id).first()

    block_data = build_block_data(
        batch_id=batch.id,
        kode_batch=batch.kode_batch,
        kebun_id=kebun.id,
        petani_id=petani.id,
        nama_petani=petani.nama_lengkap,
        nama_kebun=kebun.nama_kebun,
        latitude=float(kebun.latitude),
        longitude=float(kebun.longitude),
        tanggal_panen=str(batch.tanggal_panen),
        varietas_nanas=kebun.varietas_nanas or "Simadu",
        jenis_pupuk=kebun.jenis_pupuk,
        total_buah=batch.total_buah,
        jumlah_grade_a=batch.jumlah_grade_a,
        jumlah_grade_b=batch.jumlah_grade_b,
        jumlah_grade_c=batch.jumlah_grade_c,
        jumlah_reject=batch.jumlah_reject,
        total_berat_kg=float(batch.total_berat_kg or 0),
    )

    existing = db.query(TraceabilityBlockchain).filter(
        TraceabilityBlockchain.batch_id == batch.id
    ).first()

    if existing:
        # Refresh block yang sudah ada dengan data terbaru.
        new_hash = compute_hash(block_data, existing.previous_hash)
        existing.block_data = block_data
        existing.block_hash = new_hash
        existing.is_valid = True
        db.commit()
        db.refresh(existing)
        return existing

    # Belum ada block untuk batch ini -> buat block baru di ujung chain.
    last_block = (
        db.query(TraceabilityBlockchain)
        .order_by(TraceabilityBlockchain.block_index.desc())
        .first()
    )
    block_index = (last_block.block_index + 1) if last_block else 0
    previous_hash = last_block.block_hash if last_block else GENESIS_HASH
    block_hash = compute_hash(block_data, previous_hash)

    block = TraceabilityBlockchain(
        batch_id=batch.id,
        block_data=block_data,
        block_hash=block_hash,
        previous_hash=previous_hash,
        block_index=block_index,
    )
    db.add(block)
    db.commit()
    db.refresh(block)
    return block


def verify_block(db: Session, batch_id: int) -> dict:
    """
    Verifikasi integritas block milik satu batch.

    Menghitung ulang hash dari block_data + previous_hash yang tersimpan,
    lalu membandingkan dengan block_hash yang tersimpan di DB.
    Jika berbeda berarti block_data sudah diubah manual di luar aplikasi
    (indikasi manipulasi data).
    """
    block = db.query(TraceabilityBlockchain).filter(
        TraceabilityBlockchain.batch_id == batch_id
    ).first()

    if not block:
        return {"found": False, "is_valid": None, "detail": "Block tidak ditemukan untuk batch ini."}

    recomputed_hash = compute_hash(block.block_data, block.previous_hash)
    is_valid = recomputed_hash == block.block_hash

    # Simpan status validasi terbaru ke DB
    block.is_valid = is_valid
    db.commit()

    return {
        "found": True,
        "is_valid": is_valid,
        "block_index": block.block_index,
        "block_hash": block.block_hash,
        "recomputed_hash": recomputed_hash,
        "detail": "Data konsisten, tidak ada indikasi manipulasi." if is_valid
                  else "PERINGATAN: hash tidak cocok — data kemungkinan telah diubah di luar sistem.",
    }
