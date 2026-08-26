from sqlalchemy import Boolean, Column, Date, DateTime, Numeric, ForeignKey, Integer, String, func

from app.database.base import Base


class Kebun(Base):
    __tablename__ = "kebun"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    petani_id           = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    nama_kebun          = Column(String(100), nullable=False)
    kecamatan           = Column(String(50), nullable=True, index=True)  # cth: Jalancagak, Cijambe, Cirangkong
    varietas_nanas      = Column(String(50), default="Simadu")
    jenis_bibit         = Column(String(50), default="Lokal")
    jenis_pupuk         = Column(String(100), nullable=True)
    tanggal_tanam       = Column(Date, nullable=True)
    latitude            = Column(Numeric(10, 8), nullable=False)
    longitude           = Column(Numeric(11, 8), nullable=False)
    luas_lahan_hektar   = Column(Numeric(5, 2), nullable=True)
    is_active           = Column(Boolean, default=True)
    created_at          = Column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"<Kebun id={self.id} nama={self.nama_kebun} petani_id={self.petani_id}>"