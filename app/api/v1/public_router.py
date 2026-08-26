from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.batch import BatchPanen
from app.models.blockchain import TraceabilityBlockchain
from app.models.grading import GradingNanas
from app.services.traceability_service import verify_block

router = APIRouter(prefix="/public", tags=["Public Traceability"])


@router.get("/trace/{kode_batch}")
def trace_batch(kode_batch: str, db: Session = Depends(get_db)):
    """
    Endpoint publik (TANPA LOGIN) yang dituju saat QR code di kemasan
    nanas di-scan oleh pembeli/eksportir/Dinas Pertanian.

    Mengembalikan ringkasan traceability batch: asal kebun, tanggal panen,
    komposisi grade, serta status verifikasi integritas blockchain-nya.
    Tidak mengembalikan data sensitif (kontak pribadi petani, dsb).
    """
    batch = db.query(BatchPanen).filter(BatchPanen.kode_batch == kode_batch).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Kode batch tidak ditemukan.")

    block = db.query(TraceabilityBlockchain).filter(
        TraceabilityBlockchain.batch_id == batch.id
    ).first()

    verification = verify_block(db, batch.id)

    grading_count = db.query(GradingNanas).filter(GradingNanas.batch_id == batch.id).count()

    return {
        "kode_batch": batch.kode_batch,
        "tanggal_panen": batch.tanggal_panen,
        "status_distribusi": batch.status_distribusi,
        "rekap_grade": {
            "total_buah": batch.total_buah,
            "grade_a_ekspor": batch.jumlah_grade_a,
            "grade_b_premium_lokal": batch.jumlah_grade_b,
            "grade_c_standar": batch.jumlah_grade_c,
            "reject": batch.jumlah_reject,
        },
        "total_scan_grading": grading_count,
        "asal": {
                    "nama_kebun": block.block_data.get("kebun", {}).get("nama") if block else None,
                    "lokasi_gps": {
                        "latitude": block.block_data.get("kebun", {}).get("latitude") if block else None,
                        "longitude": block.block_data.get("kebun", {}).get("longitude") if block else None,
                    },
                    "varietas_nanas": block.block_data.get("kebun", {}).get("varietas") if block else None,
        },
        "verifikasi_integritas": {
            "is_valid": verification.get("is_valid"),
            "keterangan": verification.get("detail"),
        },
    }
