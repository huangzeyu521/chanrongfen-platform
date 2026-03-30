import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from ..core.database import Base

class Voucher(Base):
    __tablename__ = "vouchers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)  # enterprise/expert
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    score_dim: Mapped[str] = mapped_column(String(50), nullable=False)
    file_name: Mapped[str] = mapped_column(String(200), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=True)
    file_type: Mapped[str] = mapped_column(String(20), nullable=True)
    # status: 0=pending, 1=approved, 2=rejected
    status: Mapped[int] = mapped_column(Integer, default=0)
    review_comment: Mapped[str] = mapped_column(String(500), nullable=True)
    reviewer_id: Mapped[str] = mapped_column(String(36), nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    uploaded_by: Mapped[str] = mapped_column(String(36), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
