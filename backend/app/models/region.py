import uuid
from datetime import datetime, date
from sqlalchemy import String, DateTime, Date, Float, Integer, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from ..core.database import Base

class Region(Base):
    __tablename__ = "regions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    province: Mapped[str] = mapped_column(String(20), nullable=False)
    city: Mapped[str] = mapped_column(String(20), nullable=True)
    industry_focus: Mapped[str] = mapped_column(Text, nullable=True)   # JSON array stored as text
    scale_require: Mapped[str] = mapped_column(String(50), nullable=True)
    tech_require: Mapped[str] = mapped_column(String(200), nullable=True)
    finance_scale: Mapped[str] = mapped_column(String(100), nullable=True)
    credit_require: Mapped[float] = mapped_column(Float, default=0.0)
    contact_person: Mapped[str] = mapped_column(String(50), nullable=True)
    contact_phone: Mapped[str] = mapped_column(String(20), nullable=True)
    status: Mapped[int] = mapped_column(Integer, default=1)
    expire_date: Mapped[date] = mapped_column(Date, nullable=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
