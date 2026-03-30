import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from ..core.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(60), nullable=False)
    # roles: admin, enterprise, gov, finance, expert, operator
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="enterprise")
    real_name: Mapped[str] = mapped_column(String(50), nullable=True)
    avatar_url: Mapped[str] = mapped_column(String(500), nullable=True)
    # status: 1=active, 0=disabled, 2=pending
    status: Mapped[int] = mapped_column(Integer, default=1)
    last_login_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
