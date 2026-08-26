"""
Blockchain Hash Service — Pembuatan dan validasi hash SHA-256 untuk traceability.

Konsep:
- Setiap batch panen memiliki satu "block" dalam chain.
- Hash setiap block dibuat dari: data batch (snapshot) + previous_hash.
- Jika data diubah, hash berubah dan chain menjadi invalid.
- Chain bersifat global dan kronologis (block_index berurutan).
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Optional


GENESIS_HASH = "0" * 64  # Hash awal (tidak ada block sebelumnya)


def _serialize(data: dict) -> str:
    """Serialisasi dict ke JSON deterministik (key diurutkan)."""
    return json.dumps(data, sort_keys=True, ensure_ascii=False, default=str)


def compute_hash(block_data: dict, previous_hash: str) -> str:
    """
    Hitung SHA-256 hash dari data block + previous_hash.
    
    Args:
        block_data: Snapshot data batch yang akan di-hash.
        previous_hash: Hash dari block sebelumnya.
    
    Returns:
        SHA-256 hash sebagai hex string (64 karakter).
    """
    content = _serialize({
        "block_data": block_data,
        "previous_hash": previous_hash,
    })
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def build_block_data(
    batch_id: int,
    kode_batch: str,
    kebun_id: int,
    petani_id: int,
    nama_petani: str,
    nama_kebun: str,
    latitude: float,
    longitude: float,
    tanggal_panen: str,       # Format ISO: YYYY-MM-DD
    varietas_nanas: str,
    jenis_pupuk: Optional[str],
    total_buah: int,
    jumlah_grade_a: int,
    jumlah_grade_b: int,
    jumlah_grade_c: int,
    jumlah_reject: int,
    total_berat_kg: float,
    timestamp_created: Optional[str] = None,
) -> dict:
    """
    Buat snapshot data yang akan disimpan di block.
    
    Semua field di sini adalah yang tertera di QR Code traceability.
    Sesuai kebutuhan yang disebutkan Kepala Bidang Hortikultura Dinas Pertanian Subang.
    """
    return {
        "batch_id":         batch_id,
        "kode_batch":       kode_batch,
        "petani": {
            "id":           petani_id,
            "nama":         nama_petani,
        },
        "kebun": {
            "id":           kebun_id,
            "nama":         nama_kebun,
            "latitude":     latitude,
            "longitude":    longitude,
            "varietas":     varietas_nanas,
            "jenis_pupuk":  jenis_pupuk,
        },
        "panen": {
            "tanggal":      tanggal_panen,
            "total_buah":   total_buah,
            "total_berat_kg": total_berat_kg,
        },
        "grading_summary": {
            "grade_a":      jumlah_grade_a,
            "grade_b":      jumlah_grade_b,
            "grade_c":      jumlah_grade_c,
            "reject":       jumlah_reject,
        },
        "timestamp_created": timestamp_created or datetime.now(timezone.utc).isoformat(),
    }


def verify_block(block_data: dict, stored_hash: str, previous_hash: str) -> bool:
    """
    Verifikasi integritas satu block.
    
    Hitung ulang hash dari block_data + previous_hash,
    lalu bandingkan dengan hash yang tersimpan di DB.
    
    Returns:
        True jika data tidak dimanipulasi, False jika ada perubahan.
    """
    expected_hash = compute_hash(block_data, previous_hash)
    return expected_hash == stored_hash
