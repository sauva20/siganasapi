from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.user_schema import LoginRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Login menggunakan username dan password.
    Mengembalikan JWT access token jika berhasil.
    """
    user = db.query(User).filter(
        User.username == payload.username,
        User.is_active == True
    ).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah.",
        )

    token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.JWT_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


# @router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
# def register(payload: UserCreate, db: Session = Depends(get_db)):
#     """
#     Registrasi pengguna baru.
#     Username harus unik.
#     """
#     existing = db.query(User).filter(User.username == payload.username).first()
#     if existing:
#         raise HTTPException(
#             status_code=status.HTTP_409_CONFLICT,
#             detail=f"Username '{payload.username}' sudah digunakan.",
#         )

#     new_user = User(
#         username=payload.username,
#         password_hash=hash_password(payload.password),
#         nama_lengkap=payload.nama_lengkap,
#         no_hp=payload.no_hp,
#         role=payload.role,
#     )
#     db.add(new_user)
#     db.commit()
#     db.refresh(new_user)

#     return new_user


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Mendapatkan data profil pengguna yang sedang login."""
    return current_user
