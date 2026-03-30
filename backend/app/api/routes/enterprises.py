from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from ...core.database import get_db
from ...models.enterprise import Enterprise
from ..deps import get_current_user, require_admin
from ...models.user import User
import uuid

router = APIRouter(prefix="/enterprises", tags=["企业管理"])

class EnterpriseCreate(BaseModel):
    name: str
    unified_code: Optional[str] = None
    legal_person: Optional[str] = None
    registered_capital: Optional[float] = None
    industry: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    founded_year: Optional[int] = None
    employee_count: Optional[int] = None
    description: Optional[str] = None

class ScoreUpdate(BaseModel):
    operation_score: Optional[float] = None
    innovation_score: Optional[float] = None
    credit_score: Optional[float] = None
    growth_score: Optional[float] = None

class EnterpriseOut(BaseModel):
    id: str
    name: str
    unified_code: Optional[str]
    legal_person: Optional[str]
    industry: Optional[str]
    province: Optional[str]
    city: Optional[str]
    employee_count: Optional[int]
    total_score: float
    operation_score: float
    innovation_score: float
    credit_score: float
    growth_score: float
    status: int
    created_at: str

    @classmethod
    def from_orm(cls, e: Enterprise):
        return cls(
            id=e.id, name=e.name, unified_code=e.unified_code,
            legal_person=e.legal_person, industry=e.industry,
            province=e.province, city=e.city,
            employee_count=e.employee_count,
            total_score=e.total_score, operation_score=e.operation_score,
            innovation_score=e.innovation_score, credit_score=e.credit_score,
            growth_score=e.growth_score, status=e.status,
            created_at=e.created_at.isoformat() if e.created_at else ""
        )

def _calc_total(e: Enterprise) -> float:
    return round(e.operation_score + e.innovation_score + e.credit_score + e.growth_score, 1)

@router.get("", summary="企业列表")
async def list_enterprises(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    score_min: Optional[float] = None,
    province: Optional[str] = None,
    industry: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Enterprise).where(Enterprise.is_deleted == False)
    if keyword:
        query = query.where(Enterprise.name.contains(keyword))
    if score_min is not None:
        query = query.where(Enterprise.total_score >= score_min)
    if province:
        query = query.where(Enterprise.province == province)
    if industry:
        query = query.where(Enterprise.industry == industry)
    # Non-admin can only see active enterprises
    if current_user.role not in ("admin", "operator"):
        query = query.where(Enterprise.status == 1)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar()
    ents = (await db.execute(
        query.order_by(Enterprise.total_score.desc())
             .offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()

    return {"total": total, "items": [EnterpriseOut.from_orm(e) for e in ents]}

@router.post("", summary="创建企业", status_code=201)
async def create_enterprise(
    data: EnterpriseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ent = Enterprise(
        id=str(uuid.uuid4()),
        **data.model_dump(exclude_none=True),
        user_id=current_user.id
    )
    db.add(ent)
    await db.commit()
    return EnterpriseOut.from_orm(ent)

@router.get("/{ent_id}", summary="企业详情")
async def get_enterprise(
    ent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ent = (await db.execute(
        select(Enterprise).where(Enterprise.id == ent_id, Enterprise.is_deleted == False)
    )).scalar_one_or_none()
    if not ent:
        raise HTTPException(status_code=404, detail="企业不存在")
    return EnterpriseOut.from_orm(ent)

@router.get("/{ent_id}/score", summary="获取企业评分")
async def get_score(
    ent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ent = (await db.execute(
        select(Enterprise).where(Enterprise.id == ent_id, Enterprise.is_deleted == False)
    )).scalar_one_or_none()
    if not ent:
        raise HTTPException(status_code=404, detail="企业不存在")
    return {
        "enterprise_id": ent.id,
        "enterprise_name": ent.name,
        "total_score": ent.total_score,
        "operation_score": ent.operation_score,
        "innovation_score": ent.innovation_score,
        "credit_score": ent.credit_score,
        "growth_score": ent.growth_score,
        "score_updated_at": ent.score_updated_at.isoformat() if ent.score_updated_at else None,
        "grade": _get_grade(ent.total_score)
    }

def _get_grade(score: float) -> str:
    if score >= 800: return "S"
    if score >= 650: return "A"
    if score >= 500: return "B"
    if score >= 350: return "C"
    return "D"

@router.post("/{ent_id}/score", summary="更新企业评分")
async def update_score(
    ent_id: str,
    data: ScoreUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ent = (await db.execute(
        select(Enterprise).where(Enterprise.id == ent_id, Enterprise.is_deleted == False)
    )).scalar_one_or_none()
    if not ent:
        raise HTTPException(status_code=404, detail="企业不存在")

    # Permission: admin or the enterprise's own user
    if current_user.role not in ("admin",) and ent.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权限更新此企业评分")

    # Validate ranges
    if data.operation_score is not None:
        if not 0 <= data.operation_score <= 400:
            raise HTTPException(status_code=422, detail="经营维度评分范围 0-400")
        ent.operation_score = data.operation_score
    if data.innovation_score is not None:
        if not 0 <= data.innovation_score <= 300:
            raise HTTPException(status_code=422, detail="创新维度评分范围 0-300")
        ent.innovation_score = data.innovation_score
    if data.credit_score is not None:
        if not 0 <= data.credit_score <= 200:
            raise HTTPException(status_code=422, detail="信用维度评分范围 0-200")
        ent.credit_score = data.credit_score
    if data.growth_score is not None:
        if not 0 <= data.growth_score <= 100:
            raise HTTPException(status_code=422, detail="发展维度评分范围 0-100")
        ent.growth_score = data.growth_score

    ent.total_score = _calc_total(ent)
    ent.score_updated_at = datetime.utcnow()
    await db.commit()
    return {"message": "评分更新成功", "total_score": ent.total_score}

@router.delete("/{ent_id}", summary="删除企业", status_code=204)
async def delete_enterprise(
    ent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    ent = (await db.execute(
        select(Enterprise).where(Enterprise.id == ent_id)
    )).scalar_one_or_none()
    if not ent:
        raise HTTPException(status_code=404, detail="企业不存在")
    ent.is_deleted = True
    await db.commit()
