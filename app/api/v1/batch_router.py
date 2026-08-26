import io
import random
import string
from datetime import date

import qrcode
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_roles
from app.core.config import settings
from app.models.batch import BatchPanen, StatusDistribusiEnum
from app.models.kebun import Kebun
from app.models.user import RoleEnum, User
from app.schemas.batch_schema import BatchCreate, BatchResponse, BatchUpdateStatus
from app.services.traceability_service import sync_block, verify_block

router = APIRouter(prefix="/batches", tags=["Batch Panen"])


def _generate_kode_batch(tanggal_panen: date) -> str:
    """Generate kode batch: BATCH-YYYYMMDD-XXXX (XXXX = 4 karakter acak)."""
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"BATCH-{tanggal_panen.strftime('%Y%m%d')}-{suffix}"


def _generate_kode_qr(kode_batch: str) -> str:
    """
    QR Code berisi URL ke halaman traceability publik.
    Format: /public/trace/{kode_batch}
    """
    return f"/public/trace/{kode_batch}"


@router.post("/", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
def create_batch(
    payload: BatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.dinas_pertanian)),
):
    """
    Buat batch panen baru.
    Hanya petani dan pengepul yang dapat membuat batch.
    """
    # Validasi: kebun harus milik petani yang login
    kebun = db.query(Kebun).filter(Kebun.id == payload.kebun_id, Kebun.is_active == True).first()
    if not kebun:
        raise HTTPException(status_code=404, detail="Kebun tidak ditemukan.")


    # Buat kode batch yang unik
    while True:
        kode_batch = _generate_kode_batch(payload.tanggal_panen)
        exists = db.query(BatchPanen).filter(BatchPanen.kode_batch == kode_batch).first()
        if not exists:
            break

    kode_qr = _generate_kode_qr(kode_batch)

    batch = BatchPanen(
        kebun_id=payload.kebun_id,
        kode_batch=kode_batch,
        kode_qr=kode_qr,
        tanggal_panen=payload.tanggal_panen,
        catatan=payload.catatan,
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)

    # Buat block blockchain awal untuk batch ini (total masih 0, akan
    # di-refresh otomatis setiap ada grading baru masuk — lihat yolo_router).
    sync_block(db, batch)

    return batch


@router.get("/", response_model=list[BatchResponse])
def list_batches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Ambil daftar batch. Petani hanya melihat batch miliknya sendiri.
    Role lain melihat semua batch.
    """
    query = db.query(BatchPanen)

    return query.order_by(BatchPanen.created_at.desc()).all()


@router.get("/{batch_id}", response_model=BatchResponse)
def get_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ambil detail satu batch berdasarkan ID."""
    batch = db.query(BatchPanen).filter(BatchPanen.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch tidak ditemukan.")
    return batch


@router.patch("/{batch_id}/status", response_model=BatchResponse)
def update_batch_status(
    batch_id: int,
    payload: BatchUpdateStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.dinas_pertanian)),
):
    """Update status distribusi batch. Hanya pengepul dan dinas pertanian."""
    batch = db.query(BatchPanen).filter(BatchPanen.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch tidak ditemukan.")

    if payload.status_distribusi == StatusDistribusiEnum.di_pengepul and not (
        payload.pengepul_id or batch.pengepul_id
    ):
        # Validasi yang sebelumnya cuma jadi komentar di schema, sekarang ditegakkan.
        raise HTTPException(
            status_code=422,
            detail="pengepul_id wajib diisi saat status diubah menjadi 'di_pengepul'.",
        )

    batch.status_distribusi = payload.status_distribusi
    if payload.pengepul_id:
        batch.pengepul_id = payload.pengepul_id

    db.commit()
    db.refresh(batch)

    # Refresh block blockchain supaya status distribusi terbaru ikut tercatat.
    sync_block(db, batch)

    return batch


@router.get("/{batch_id}/verify")
def verify_batch_integrity(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Verifikasi integritas data batch terhadap block blockchain-nya.
    Dipakai Dinas Pertanian / eksportir untuk mengecek apakah data
    traceability batch ini pernah diubah di luar sistem.
    """
    batch = db.query(BatchPanen).filter(BatchPanen.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch tidak ditemukan.")

    return verify_block(db, batch_id)


@router.get("/{batch_id}/qrcode")
def get_batch_qrcode(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate gambar QR Code (PNG) untuk ditempel/dicetak pada kemasan batch.
    QR berisi URL publik ke halaman traceability (tidak perlu login untuk
    dibuka oleh pembeli/eksportir), lihat public_router.py.
    """
    batch = db.query(BatchPanen).filter(BatchPanen.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch tidak ditemukan.")

    trace_url = f"{settings.PUBLIC_BASE_URL}/public/trace/{batch.kode_batch}"

    img = qrcode.make(trace_url)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return StreamingResponse(buffer, media_type="image/png")
