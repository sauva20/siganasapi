from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.user import RoleEnum


# ---- Request Schemas ----

class UserCreate(BaseModel):
    username:       str = Field(..., min_length=3, max_length=50, examples=["petani_budi"])
    password:       str = Field(..., min_length=6, examples=["password123"])
    nama_lengkap:   str = Field(..., max_length=100, examples=["Budi Santoso"])
    no_hp:          Optional[str] = Field(None, max_length=15, examples=["081234567890"])
    role:           RoleEnum


class UserUpdate(BaseModel):
    nama_lengkap:   Optional[str] = Field(None, max_length=100)
    no_hp:          Optional[str] = Field(None, max_length=15)
    is_active:      Optional[bool] = None


# ---- Response Schemas ----

class UserResponse(BaseModel):
    id:             int
    username:       str
    nama_lengkap:   str
    no_hp:          Optional[str]
    role:           RoleEnum
    is_active:      bool
    created_at:     datetime

    model_config = {"from_attributes": True}


# ---- Auth Schemas ----

class LoginRequest(BaseModel):
    username:   str = Field(..., examples=["petani_budi"])
    password:   str = Field(..., examples=["password123"])


class TokenResponse(BaseModel):
    access_token:   str
    token_type:     str = "bearer"
    expires_in:     int     # Dalam detik
    user:           UserResponse
