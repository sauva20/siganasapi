import enum
from sqlalchemy import Column, Date, DateTime, Numeric, Enum, ForeignKey, Integer, String, Text, func

from app.database.base import Base


class StatusDistribusiEnum(str, enum.Enum):
    di_lahan            = "di_lahan"
    di_pengepul         = "di_pengepul"
    terkirim_industri   = "terkirim_industri"
    terekspor           = "terekspor"


class BatchPanen(Base):
    __tablename__ = "batch_panen"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    kebun_id            = Column(Integer, ForeignKey("kebun.id", ondelete="CASCADE"), nullable=False, index=True)
    pengepul_id         = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    kode_batch          = Column(String(20), unique=True, nullable=False)   # BATCH-YYYYMMDD-XXXX
    kode_qr             = Column(String(255), unique=True, nullable=False)  # Data/URL untuk QR Code
    tanggal_panen       = Column(Date, nullable=False, index=True)
    catatan             = Column(Text, nullable=True)
    status_distribusi   = Column(Enum(StatusDistribusiEnum), default=StatusDistribusiEnum.di_lahan, index=True)

    # Rekapitulasi — diupdate otomatis setiap ada grading baru
    total_buah          = Column(Integer, default=0)
    total_berat_kg      = Column(Numeric(10, 2), default=0.00)
    jumlah_grade_a      = Column(Integer, default=0)
    jumlah_grade_b      = Column(Integer, default=0)
    jumlah_grade_c      = Column(Integer, default=0)
    jumlah_reject       = Column(Integer, default=0)

    created_at          = Column(DateTime, server_default=func.now())
    updated_at          = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<BatchPanen id={self.id} kode={self.kode_batch} status={self.status_distribusi}>"