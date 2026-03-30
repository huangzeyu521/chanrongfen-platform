import uuid
from datetime import datetime, date
from sqlalchemy import String, DateTime, Date, Float, Text
from sqlalchemy.orm import Mapped, mapped_column
from ..core.database import Base

class Docking(Base):
    __tablename__ = "dockings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # type: ENT_GOV / ENT_FIN / EXP_GOV / MEM_ACT
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    initiator_id: Mapped[str] = mapped_column(String(36), nullable=False)
    target_id: Mapped[str] = mapped_column(String(36), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    match_score: Mapped[float] = mapped_column(Float, default=0.0)
    # status: draft/submitted/approved/ongoing/completed/cancelled
    status: Mapped[str] = mapped_column(String(20), default="draft")
    result: Mapped[str] = mapped_column(Text, nullable=True)
    apply_date: Mapped[date] = mapped_column(Date, nullable=True)
    complete_date: Mapped[date] = mapped_column(Date, nullable=True)
    reviewer_id: Mapped[str] = mapped_column(String(36), nullable=True)
    remark: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
