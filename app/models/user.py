import enum
from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String, func

from app.database.base import Base


class RoleEnum(str, enum.Enum):
    petani = "petani"
    pengepul = "pengepul"
    eksportir = "eksportir"
    pabrik = "pabrik"
    dinas_pertanian = "dinas_pertanian"


class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    username      = Column(String(50), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    nama_lengkap  = Column(String(100), nullable=False)
    no_hp         = Column(String(15), nullable=True)
    role          = Column(Enum(RoleEnum), nullable=False)
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime, server_default=func.now())
    updated_at    = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username} role={self.role}>"
