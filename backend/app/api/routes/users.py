from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from ...core.database import get_db
from ...core.security import get_password_hash
from ...models.user import User
from ..deps import get_current_user, require_admin
import uuid

router = APIRouter(prefix="/users", tags=["用户管理"])

class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: str = "enterprise"
    real_name: Optional[str] = None

class UserUpdate(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    real_name: Optional[str] = None
    status: Optional[int] = None

class UserOut(BaseModel):
    id: str
    username: str
    email: Optional[str]
    phone: Optional[str]
    role: str
    real_name: Optional[str]
    status: int
    created_at: str

    @classmethod
    def from_orm(cls, u: User):
        return cls(
            id=u.id, username=u.username, email=u.email,
            phone=u.phone, role=u.role, real_name=u.real_name,
            status=u.status,
            created_at=u.created_at.isoformat() if u.created_at else ""
        )

@router.get("", summary="用户列表")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    role: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    query = select(User).where(User.is_deleted == False)
    if keyword:
        query = query.where(User.username.contains(keyword))
    if role:
        query = query.where(User.role == role)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar()

    users = (await db.execute(
        query.offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()

    return {"total": total, "items": [UserOut.from_orm(u) for u in users]}

@router.post("", summary="创建用户", status_code=201)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    exists = (await db.execute(
        select(User).where(User.username == data.username)
    )).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=409, detail="用户名已存在")

    user = User(
        id=str(uuid.uuid4()),
        username=data.username,
        password_hash=get_password_hash(data.password),
        email=data.email,
        phone=data.phone,
        role=data.role,
        real_name=data.real_name
    )
    db.add(user)
    await db.commit()
    return UserOut.from_orm(user)

@router.get("/me", summary="获取当前用户信息")
async def get_me(current_user: User = Depends(get_current_user)):
    return UserOut.from_orm(current_user)

@router.get("/{user_id}", summary="用户详情")
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="无权限")
    user = (await db.execute(
        select(User).where(User.id == user_id, User.is_deleted == False)
    )).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return UserOut.from_orm(user)

@router.put("/{user_id}", summary="更新用户")
async def update_user(
    user_id: str,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="无权限")
    user = (await db.execute(
        select(User).where(User.id == user_id, User.is_deleted == False)
    )).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(user, field, value)
    await db.commit()
    return UserOut.from_orm(user)

@router.delete("/{user_id}", summary="删除用户", status_code=204)
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    user = (await db.execute(
        select(User).where(User.id == user_id)
    )).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.is_deleted = True
    await db.commit()
