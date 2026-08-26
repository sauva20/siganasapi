from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from app.models.batch import StatusDistribusiEnum


class BatchCreate(BaseModel):
    kebun_id:       int = Field(..., examples=[1])
    tanggal_panen:  date = Field(..., examples=["2026-05-01"])
    catatan:        Optional[str] = Field(None, examples=["Panen sesi pagi, cuaca cerah"])


class BatchUpdateStatus(BaseModel):
    status_distribusi:  StatusDistribusiEnum
    pengepul_id:        Optional[int] = None  # Wajib diisi jika status pindah ke di_pengepul


class BatchResponse(BaseModel):
    id:                 int
    kebun_id:           int
    pengepul_id:        Optional[int]
    kode_batch:         str
    kode_qr:            str
    tanggal_panen:      date
    catatan:            Optional[str]
    status_distribusi:  StatusDistribusiEnum
    total_buah:         int
    total_berat_kg:     Decimal
    jumlah_grade_a:     int
    jumlah_grade_b:     int
    jumlah_grade_c:     int
    jumlah_reject:      int
    created_at:         datetime
    updated_at:         datetime

    model_config = {"from_attributes": True}
