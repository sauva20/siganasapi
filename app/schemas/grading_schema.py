from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.models.grading import GradeMutuEnum, KondisiMahkotaEnum, UkuranEnum, WarnaKulitEnum


# ---- Request: Data manual tambahan saat upload foto ----
class GradingManualInput(BaseModel):
    """
    Data opsional yang bisa dikirim bersama foto.
    Diisi jika petani mengukur dengan refraktometer atau timbangan.
    """
    input_brix_manual:      Optional[Decimal] = Field(None, examples=[14.5])
    input_berat_manual_kg:  Optional[Decimal] = Field(None, examples=[1.45])


# ---- Response: Hasil grading satu buah nanas ----
class GradingResponse(BaseModel):
    id:                     int
    batch_id:               int
    foto_url:               str

    # Input manual
    input_brix_manual:      Optional[Decimal]
    input_berat_manual_kg:  Optional[Decimal]

    # Output AI
    confidence_score:       Decimal
    yolo_raw_output:        Optional[Any]  # JSON bebas
    deteksi_ukuran:         Optional[UkuranEnum]
    deteksi_warna_kulit:    Optional[WarnaKulitEnum]
    deteksi_kematangan_pct: Optional[int]
    kondisi_mahkota:        Optional[KondisiMahkotaEnum]
    kondisi_defect:         Optional[str]

    # Output DSS
    grade_mutu:             GradeMutuEnum
    rekomendasi_pasar:      Optional[str]
    estimasi_harga_min:     Optional[Decimal]
    estimasi_harga_max:     Optional[Decimal]

    scanned_at:             datetime

    model_config = {"from_attributes": True}


# ---- Response ringkas untuk list view ----
class GradingSummary(BaseModel):
    id:                 int
    foto_url:           str
    grade_mutu:         GradeMutuEnum
    confidence_score:   Decimal
    rekomendasi_pasar:  Optional[str]
    scanned_at:         datetime

    model_config = {"from_attributes": True}
