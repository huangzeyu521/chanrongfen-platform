from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from ...core.database import get_db
from ...models.docking import Docking
from ..deps import get_current_user, require_admin
from ...models.user import User
import uuid

router = APIRouter(prefix="/dockings", tags=["对接管理"])

VALID_STATUSES = {"draft", "submitted", "approved", "ongoing", "completed", "cancelled"}
VALID_TYPES = {"ENT_GOV", "ENT_FIN", "EXP_GOV", "MEM_ACT"}

class DockingCreate(BaseModel):
    type: str
    initiator_id: str
    target_id: str
    title: str
    description: Optional[str] = None
    match_score: float = 0.0
    apply_date: Optional[str] = None

class StatusUpdate(BaseModel):
    status: str
    remark: Optional[str] = None
    result: Optional[str] = None

class DockingOut(BaseModel):
    id: str
    type: str
    initiator_id: str
    target_id: str
    title: str
    description: Optional[str]
    match_score: float
    status: str
    result: Optional[str]
    apply_date: Optional[str]
    complete_date: Optional[str]
    remark: Optional[str]
    created_at: str

    @classmethod
    def from_orm(cls, d: Docking):
        return cls(
            id=d.id, type=d.type, initiator_id=d.initiator_id,
            target_id=d.target_id, title=d.title, description=d.description,
            match_score=d.match_score, status=d.status, result=d.result,
            apply_date=d.apply_date.isoformat() if d.apply_date else None,
            complete_date=d.complete_date.isoformat() if d.complete_date else None,
            remark=d.remark,
            created_at=d.created_at.isoformat() if d.created_at else ""
        )

@router.get("", summary="对接申请列表")
async def list_dockings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    type: Optional[str] = None,
    initiator_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Docking)
    if status:
        query = query.where(Docking.status == status)
    if type:
        query = query.where(Docking.type == type)
    if initiator_id:
        query = query.where(Docking.initiator_id == initiator_id)
    # Non-admin: filter by relevant records
    if current_user.role not in ("admin", "operator"):
        query = query.where(
            (Docking.initiator_id == current_user.id) |
            (Docking.target_id == current_user.id)
        )

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar()
    dockings = (await db.execute(
        query.order_by(Docking.created_at.desc())
             .offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()

    return {"total": total, "items": [DockingOut.from_orm(d) for d in dockings]}

@router.post("", summary="创建对接申请", status_code=201)
async def create_docking(
    data: DockingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if data.type not in VALID_TYPES:
        raise HTTPException(status_code=422, detail=f"对接类型无效，可选：{VALID_TYPES}")

    from datetime import date
    docking = Docking(
        id=str(uuid.uuid4()),
        type=data.type,
        initiator_id=data.initiator_id,
        target_id=data.target_id,
        title=data.title,
        description=data.description,
        match_score=data.match_score,
        status="draft",
        apply_date=date.fromisoformat(data.apply_date) if data.apply_date else date.today()
    )
    db.add(docking)
    await db.commit()
    return DockingOut.from_orm(docking)

@router.get("/{docking_id}", summary="对接详情")
async def get_docking(
    docking_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    d = (await db.execute(
        select(Docking).where(Docking.id == docking_id)
    )).scalar_one_or_none()
    if not d:
        raise HTTPException(status_code=404, detail="对接申请不存在")
    return DockingOut.from_orm(d)

@router.patch("/{docking_id}/status", summary="更新对接状态")
async def update_status(
    docking_id: str,
    data: StatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if data.status not in VALID_STATUSES:
        raise HTTPException(status_code=422, detail=f"状态无效，可选：{VALID_STATUSES}")

    d = (await db.execute(
        select(Docking).where(Docking.id == docking_id)
    )).scalar_one_or_none()
    if not d:
        raise HTTPException(status_code=404, detail="对接申请不存在")

    if current_user.role not in ("admin", "operator"):
        raise HTTPException(status_code=403, detail="无权限更新对接状态")

    d.status = data.status
    if data.remark:
        d.remark = data.remark
    if data.result:
        d.result = data.result
    if data.status == "completed":
        from datetime import date
        d.complete_date = date.today()
    d.updated_at = datetime.utcnow()
    await db.commit()
    return {"message": "状态更新成功", "status": d.status}
