import os
import uuid
from pathlib import Path
from typing import Optional

import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.core.config import settings
from app.models.batch import BatchPanen
from app.models.grading import GradingNanas
from app.models.user import RoleEnum, User
from app.schemas.grading_schema import GradingResponse, GradingSummary
from app.services.traceability_service import sync_block
from app.services.yolo_engine import run_inference

router = APIRouter(prefix="/grading", tags=["Grading YOLO"])

UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _validate_file(file: UploadFile) -> None:
    """Validasi ekstensi dan ukuran file gambar."""
    ext = Path(file.filename).suffix.lstrip(".").lower()
    if ext not in settings.ALLOWED_EXTENSIONS_LIST:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Format file tidak didukung. Gunakan: {settings.ALLOWED_EXTENSIONS}",
        )


async def _save_upload(file: UploadFile) -> str:
    """Simpan file upload dengan nama unik. Kembalikan path relatif."""
    ext = Path(file.filename).suffix.lower()
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = UPLOAD_DIR / filename

    async with aiofiles.open(file_path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)

    return str(file_path)


@router.post("/{batch_id}/scan", response_model=GradingResponse, status_code=status.HTTP_201_CREATED)
async def scan_pineapple(
    batch_id: int,
    foto: UploadFile = File(..., description="Foto buah nanas (JPG/PNG/WEBP)"),
    input_brix_manual: Optional[float] = Form(None, description="Nilai Brix dari refraktometer (opsional)"),
    input_berat_manual_kg: Optional[float] = Form(None, description="Berat aktual dari timbangan kg (opsional)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.dinas_pertanian)),
):
    """
    Upload foto nanas dan jalankan grading otomatis.
    
    Flow:
    1. Validasi file → Simpan ke disk
    2. Inferensi YOLO → Deteksi atribut visual
    3. DSS → Tentukan grade dan rekomendasi pasar
    4. Simpan hasil ke DB
    5. Update rekapitulasi batch
    """
    # Validasi batch
    batch = db.query(BatchPanen).filter(BatchPanen.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch tidak ditemukan.")

    # Validasi dan simpan file
    _validate_file(foto)
    foto_path = await _save_upload(foto)

    # Inferensi YOLO + DSS
    yolo_result, dss_output = run_inference(
        image_path=foto_path,
        input_brix_manual=input_brix_manual,
        input_berat_manual_kg=input_berat_manual_kg,
    )

    # Simpan hasil ke DB
    grading = GradingNanas(
        batch_id=batch_id,
        foto_url=foto_path,
        input_brix_manual=input_brix_manual,
        input_berat_manual_kg=input_berat_manual_kg,
        confidence_score=yolo_result.get("confidence_score"),
        yolo_raw_output=yolo_result.get("raw_output"),
        deteksi_ukuran=yolo_result.get("deteksi_ukuran"),
        deteksi_warna_kulit=yolo_result.get("deteksi_warna_kulit"),
        deteksi_kematangan_pct=yolo_result.get("deteksi_kematangan_pct"),
        kondisi_mahkota=yolo_result.get("kondisi_mahkota"),
        kondisi_defect=yolo_result.get("kondisi_defect"),
        grade_mutu=dss_output.grade_mutu,
        rekomendasi_pasar=dss_output.rekomendasi_pasar,
        estimasi_harga_min=dss_output.estimasi_harga_min,
        estimasi_harga_max=dss_output.estimasi_harga_max,
    )
    db.add(grading)

    # Update rekapitulasi batch
    _update_batch_summary(db, batch, dss_output.grade_mutu, input_berat_manual_kg)

    db.commit()
    db.refresh(grading)
    db.refresh(batch)

    # Sinkronkan ulang block blockchain batch ini supaya hash-nya selalu
    # mencerminkan rekap grading terbaru (lihat traceability_service.sync_block).
    sync_block(db, batch)

    return grading


def _update_batch_summary(
    db: Session,
    batch: BatchPanen,
    grade_mutu: str,
    berat_kg: Optional[float],
) -> None:
    """Update kolom rekapitulasi di tabel batch_panen setiap ada grading baru."""
    batch.total_buah += 1

    if berat_kg:
        batch.total_berat_kg = float(batch.total_berat_kg or 0) + berat_kg

    grade_map = {
        "Grade A": "jumlah_grade_a",
        "Grade B": "jumlah_grade_b",
        "Grade C": "jumlah_grade_c",
        "Reject":  "jumlah_reject",
    }
    col = grade_map.get(grade_mutu)
    if col:
        setattr(batch, col, getattr(batch, col, 0) + 1)


@router.get("/{batch_id}/results", response_model=list[GradingSummary])
def get_grading_results(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ambil semua hasil grading untuk satu batch."""
    batch = db.query(BatchPanen).filter(BatchPanen.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch tidak ditemukan.")

    results = (
        db.query(GradingNanas)
        .filter(GradingNanas.batch_id == batch_id)
        .order_by(GradingNanas.scanned_at.desc())
        .all()
    )
    return results


@router.get("/detail/{grading_id}", response_model=GradingResponse)
def get_grading_detail(
    grading_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ambil detail hasil grading satu buah nanas."""
    grading = db.query(GradingNanas).filter(GradingNanas.id == grading_id).first()
    if not grading:
        raise HTTPException(status_code=404, detail="Data grading tidak ditemukan.")
    return grading
