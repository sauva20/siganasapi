from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.user import RoleEnum, User
from app.schemas.user_schema import UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=list[UserResponse])
def list_users(
    role: Optional[RoleEnum] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.dinas_pertanian)),
):
    """
    Daftar pengguna, opsional difilter berdasarkan role.

    Dipakai Dinas Pertanian untuk memilih petani pemilik kebun saat
    membuat data kebun baru (lihat kebun_router.create_kebun), atau
    memilih pengepul saat update status distribusi batch.

    Contoh: GET /api/v1/users/?role=petani
    """
    query = db.query(User).filter(User.is_active == True)

    if role:
        query = query.filter(User.role == role)

    return query.order_by(User.nama_lengkap.asc()).all()