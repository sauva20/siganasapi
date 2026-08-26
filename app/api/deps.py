"""
Dependency Injections — Digunakan oleh semua router via FastAPI Depends().
"""

from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database.session import SessionLocal
from app.models.user import RoleEnum, User

security = HTTPBearer()


def get_db() -> Generator:
    """
    Dependency untuk mendapatkan sesi database.
    Sesi ditutup otomatis setelah request selesai.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency untuk mendapatkan user yang sedang login.
    Validasi JWT token dari header Authorization: Bearer <token>.
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak valid atau sudah kedaluwarsa.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: int = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak mengandung identitas pengguna.",
        )

    user = db.query(User).filter(User.id == int(user_id), User.is_active == True).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Pengguna tidak ditemukan atau tidak aktif.",
        )

    return user


def require_roles(*allowed_roles: RoleEnum):
    """
    Factory dependency untuk membatasi akses berdasarkan role.
    
    Contoh penggunaan:
        @router.get("/admin-only")
        def admin_endpoint(user = Depends(require_roles(RoleEnum.dinas_pertanian))):
            ...
    """
    def _check_role(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Akses ditolak. Role yang diizinkan: {[r.value for r in allowed_roles]}",
            )
        return current_user
    return _check_role
