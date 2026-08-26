import enum
from sqlalchemy import JSON, Column, DateTime, Numeric, Enum, ForeignKey, Integer, String, func

from app.database.base import Base


class GradeMutuEnum(str, enum.Enum):
    grade_a = "Grade A"   # Mutu Ekspor
    grade_b = "Grade B"   # Mutu Premium Lokal (Supermarket)
    grade_c = "Grade C"   # Mutu Standar (Pasar Tradisional / Industri)
    reject  = "Reject"    # Pakan Ternak / Kompos


class UkuranEnum(str, enum.Enum):
    kecil   = "Kecil"
    sedang  = "Sedang"
    besar   = "Besar"


class WarnaKulitEnum(str, enum.Enum):
    hijau               = "Hijau"
    kuning_kehijauan    = "Kuning_Kehijauan"
    kuning              = "Kuning"
    oranye              = "Oranye"


class KondisiMahkotaEnum(str, enum.Enum):
    sempurna        = "Sempurna"
    cacat_rusak     = "Cacat_Rusak"


class GradingNanas(Base):
    __tablename__ = "grading_nanas"

    id                      = Column(Integer, primary_key=True, autoincrement=True)
    batch_id                = Column(Integer, ForeignKey("batch_panen.id", ondelete="CASCADE"), nullable=False, index=True)

    # --- Input dari kamera ---
    foto_url                = Column(String(255), nullable=False)

    # --- Input manual (opsional, dari alat refraktometer / timbangan) ---
    input_brix_manual       = Column(Numeric(4, 1), nullable=True)
    input_berat_manual_kg   = Column(Numeric(4, 2), nullable=True)

    # --- Output AI dari YOLOv11 ---
    confidence_score        = Column(Numeric(5, 4), nullable=False)
    yolo_raw_output         = Column(JSON, nullable=True)   # Raw prediction untuk debug/audit
    deteksi_ukuran          = Column(Enum(UkuranEnum), nullable=True)
    deteksi_warna_kulit     = Column(Enum(WarnaKulitEnum), nullable=True)
    deteksi_kematangan_pct  = Column(Integer, nullable=True)   # Estimasi % dari visual
    kondisi_mahkota         = Column(Enum(KondisiMahkotaEnum), default=KondisiMahkotaEnum.sempurna)
    kondisi_defect          = Column(String(200), default="Tidak Ada Cacat")

    # --- Output DSS (Decision Support System) ---
    grade_mutu              = Column(Enum(GradeMutuEnum), nullable=False, index=True)
    rekomendasi_pasar       = Column(String(150), nullable=True)
    estimasi_harga_min      = Column(Numeric(10, 0), nullable=True)   # Rp per kg
    estimasi_harga_max      = Column(Numeric(10, 0), nullable=True)

    scanned_at              = Column(DateTime, server_default=func.now(), index=True)

    def __repr__(self) -> str:
        return f"<GradingNanas id={self.id} grade={self.grade_mutu} batch_id={self.batch_id}>"