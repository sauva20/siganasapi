from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, func

from app.database.base import Base

GENESIS_HASH = "0" * 64  # Hash awal untuk block pertama


class TraceabilityBlockchain(Base):
    __tablename__ = "traceability_blockchain"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    batch_id        = Column(Integer, ForeignKey("batch_panen.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Snapshot data yang di-hash saat block dibuat
    block_data      = Column(JSON, nullable=False)

    # Chain integrity
    block_hash      = Column(String(64), nullable=False)
    previous_hash   = Column(String(64), nullable=False, default=GENESIS_HASH)
    block_index     = Column(Integer, nullable=False, index=True)  # Urutan block global

    # Status
    is_valid        = Column(Boolean, default=True, index=True)
    validated_at    = Column(DateTime, server_default=func.now())
    updated_at      = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<Block index={self.block_index} batch_id={self.batch_id} valid={self.is_valid}>"
