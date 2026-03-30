from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from ...core.database import get_db
from ...models.expert import Expert
from ..deps import get_current_user, require_admin
from ...models.user import User
import uuid
from datetime import datetime

router = APIRouter(prefix="/experts", tags=["专家管理"])

class ExpertCreate(BaseModel):
    name: str
    title: Optional[str] = None
    domain: Optional[str] = None
    institution: Optional[str] = None
    bio: Optional[str] = None

class ExpertScoreUpdate(BaseModel):
    capability_score: Optional[float] = None   # 0-500
    adaptability_score: Optional[float] = None # 0-300
    willingness_score: Optional[float] = None  # 0-200

class ExpertOut(BaseModel):
    id: str
    name: str
    title: Optional[str]
    domain: Optional[str]
    institution: Optional[str]
    capability_score: float
    adaptability_score: float
    willingness_score: float
    total_score: float
    grade: Optional[str]
    status: int

    @classmethod
    def from_orm(cls, e: Expert):
        return cls(
            id=e.id, name=e.name, title=e.title, domain=e.domain,
            institution=e.institution, capability_score=e.capability_score,
            adaptability_score=e.adaptability_score,
            willingness_score=e.willingness_score,
            total_score=e.total_score, grade=e.grade, status=e.status
        )

def _compute_grade(score: float) -> str:
    if score >= 750: return "S"
    if score >= 700: return "A"
    if score >= 650: return "B"
    if score >= 600: return "C"
    return "D"

@router.get("", summary="专家列表")
async def list_experts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    domain: Optional[str] = None,
    min_score: Optional[float] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Expert).where(Expert.is_deleted == False)
    if keyword:
        query = query.where(Expert.name.contains(keyword))
    if domain:
        query = query.where(Expert.domain.contains(domain))
    if min_score is not None:
        query = query.where(Expert.total_score >= min_score)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar()
    experts = (await db.execute(
        query.order_by(Expert.total_score.desc())
             .offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()
    return {"total": total, "items": [ExpertOut.from_orm(e) for e in experts]}

@router.post("", summary="创建专家", status_code=201)
async def create_expert(
    data: ExpertCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    expert = Expert(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        **data.model_dump(exclude_none=True)
    )
    db.add(expert)
    await db.commit()
    return ExpertOut.from_orm(expert)

@router.get("/{expert_id}", summary="专家详情")
async def get_expert(
    expert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    exp = (await db.execute(
        select(Expert).where(Expert.id == expert_id, Expert.is_deleted == False)
    )).scalar_one_or_none()
    if not exp:
        raise HTTPException(status_code=404, detail="专家不存在")
    return ExpertOut.from_orm(exp)

@router.post("/{expert_id}/score", summary="更新专家评分")
async def update_expert_score(
    expert_id: str,
    data: ExpertScoreUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    exp = (await db.execute(
        select(Expert).where(Expert.id == expert_id, Expert.is_deleted == False)
    )).scalar_one_or_none()
    if not exp:
        raise HTTPException(status_code=404, detail="专家不存在")

    if data.capability_score is not None:
        if not 0 <= data.capability_score <= 500:
            raise HTTPException(status_code=422, detail="专业能力评分范围 0-500")
        exp.capability_score = data.capability_score
    if data.adaptability_score is not None:
        if not 0 <= data.adaptability_score <= 300:
            raise HTTPException(status_code=422, detail="适配度评分范围 0-300")
        exp.adaptability_score = data.adaptability_score
    if data.willingness_score is not None:
        if not 0 <= data.willingness_score <= 200:
            raise HTTPException(status_code=422, detail="意愿度评分范围 0-200")
        exp.willingness_score = data.willingness_score

    exp.total_score = round(exp.capability_score + exp.adaptability_score + exp.willingness_score, 1)
    exp.grade = _compute_grade(exp.total_score)
    exp.updated_at = datetime.utcnow()
    await db.commit()
    return {"message": "专家评分更新成功", "total_score": exp.total_score, "grade": exp.grade}
