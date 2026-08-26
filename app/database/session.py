from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,       # Cek koneksi sebelum digunakan (cegah connection drop)
    pool_recycle=3600,        # Recycle koneksi setiap 1 jam
    pool_size=10,             # Jumlah koneksi di pool
    max_overflow=20,          # Koneksi tambahan di luar pool saat ramai
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
