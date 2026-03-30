import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Boolean, Float, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column
from ..core.database import Base

class Enterprise(Base):
    __tablename__ = "enterprises"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    unified_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=True)
    legal_person: Mapped[str] = mapped_column(String(50), nullable=True)
    registered_capital: Mapped[float] = mapped_column(Float, nullable=True)
    industry: Mapped[str] = mapped_column(String(50), nullable=True)
    province: Mapped[str] = mapped_column(String(20), nullable=True)
    city: Mapped[str] = mapped_column(String(20), nullable=True)
    founded_year: Mapped[int] = mapped_column(SmallInteger, nullable=True)
    employee_count: Mapped[int] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(String(2000), nullable=True)

    # Scores (0-1000 total)
    total_score: Mapped[float] = mapped_column(Float, default=0.0)
    operation_score: Mapped[float] = mapped_column(Float, default=0.0)   # max 400
    innovation_score: Mapped[float] = mapped_column(Float, default=0.0)  # max 300
    credit_score: Mapped[float] = mapped_column(Float, default=0.0)      # max 200
    growth_score: Mapped[float] = mapped_column(Float, default=0.0)      # max 100
    score_updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    user_id: Mapped[str] = mapped_column(String(36), nullable=True)
    # status: 1=active, 2=pending, 0=disabled
    status: Mapped[int] = mapped_column(Integer, default=2)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
