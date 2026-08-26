from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class KebunCreate(BaseModel):
    petani_id:              int = Field(..., examples=[2], description="ID user dengan role petani, pemilik kebun ini.")
    nama_kebun:             str = Field(..., max_length=100, examples=["Kebun Budi Blok A"])
    kecamatan:              Optional[str] = Field(None, max_length=50, examples=["Jalancagak"])
    varietas_nanas:         Optional[str] = Field("Simadu", max_length=50)
    jenis_bibit:            Optional[str] = Field("Lokal", max_length=50)
    jenis_pupuk:            Optional[str] = Field(None, max_length=100)
    tanggal_tanam:          Optional[date] = None
    latitude:               Decimal = Field(..., examples=[-6.5678])
    longitude:              Decimal = Field(..., examples=[107.9123])
    luas_lahan_hektar:      Optional[Decimal] = Field(None, examples=[2.50])


class KebunUpdate(BaseModel):
    nama_kebun:             Optional[str] = Field(None, max_length=100)
    kecamatan:              Optional[str] = Field(None, max_length=50)
    jenis_pupuk:            Optional[str] = Field(None, max_length=100)
    tanggal_tanam:          Optional[date] = None
    luas_lahan_hektar:      Optional[Decimal] = None
    is_active:              Optional[bool] = None


class KebunResponse(BaseModel):
    id:                     int
    petani_id:              int
    nama_kebun:             str
    kecamatan:              Optional[str]
    varietas_nanas:         Optional[str]
    jenis_bibit:            Optional[str]
    jenis_pupuk:            Optional[str]
    tanggal_tanam:          Optional[date]
    latitude:               Decimal
    longitude:              Decimal
    luas_lahan_hektar:      Optional[Decimal]
    is_active:              bool
    created_at:             datetime

    model_config = {"from_attributes": True}
