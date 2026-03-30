import uuid
from datetime import datetime, date
from sqlalchemy import String, DateTime, Date, Float
from sqlalchemy.orm import Mapped, mapped_column
from ..core.database import Base

class MemberContribution(Base):
    __tablename__ = "member_contributions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    enterprise_id: Mapped[str] = mapped_column(String(36), nullable=False)
    # action_type: fee_paid/recommend/activity/resource
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    action_detail: Mapped[str] = mapped_column(String(500), nullable=True)
    score_earned: Mapped[float] = mapped_column(Float, nullable=False)
    action_date: Mapped[date] = mapped_column(Date, nullable=False)
    verified_by: Mapped[str] = mapped_column(String(36), nullable=True)
    remark: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
