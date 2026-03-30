import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column
from ..core.database import Base

class Expert(Base):
    __tablename__ = "experts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=True)
    domain: Mapped[str] = mapped_column(String(100), nullable=True)
    institution: Mapped[str] = mapped_column(String(200), nullable=True)
    bio: Mapped[str] = mapped_column(String(2000), nullable=True)

    # Three-dimension scores
    capability_score: Mapped[float] = mapped_column(Float, default=0.0)    # max 500
    adaptability_score: Mapped[float] = mapped_column(Float, default=0.0)  # max 300
    willingness_score: Mapped[float] = mapped_column(Float, default=0.0)   # max 200
    total_score: Mapped[float] = mapped_column(Float, default=0.0)         # max 1000
    grade: Mapped[str] = mapped_column(String(5), nullable=True)           # S/A/B/C/D

    user_id: Mapped[str] = mapped_column(String(36), nullable=True)
    status: Mapped[int] = mapped_column(Integer, default=2)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
