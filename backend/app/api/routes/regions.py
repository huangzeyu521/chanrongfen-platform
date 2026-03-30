import json, math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from ...core.database import get_db
from ...models.region import Region
from ...models.enterprise import Enterprise
from ..deps import get_current_user
from ...models.user import User
import uuid

router = APIRouter(prefix="/regions", tags=["区域需求"])

class RegionCreate(BaseModel):
    name: str
    province: str
    city: Optional[str] = None
    industry_focus: Optional[str] = None
    scale_require: Optional[str] = None
    tech_require: Optional[str] = None
    finance_scale: Optional[str] = None
    credit_require: float = 0.0
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    expire_date: Optional[str] = None

class RegionOut(BaseModel):
    id: str
    name: str
    province: str
    city: Optional[str]
    industry_focus: Optional[str]
    scale_require: Optional[str]
    credit_require: float
    status: int
    created_at: str

    @classmethod
    def from_orm(cls, r: Region):
        return cls(
            id=r.id, name=r.name, province=r.province, city=r.city,
            industry_focus=r.industry_focus, scale_require=r.scale_require,
            credit_require=r.credit_require, status=r.status,
            created_at=r.created_at.isoformat() if r.created_at else ""
        )

def _compute_match_score(enterprise: Enterprise, region: Region) -> float:
    """
    Simple weighted similarity score (0-100).
    Real production would use a more sophisticated vector similarity algorithm.
    """
    score = 0.0

    # Industry match (30%)
    if enterprise.industry and region.industry_focus:
        try:
            industries = json.loads(region.industry_focus)
            if isinstance(industries, list) and enterprise.industry in industries:
                score += 30.0
            else:
                score += 10.0
        except Exception:
            score += 10.0
    else:
        score += 15.0  # unknown = neutral

    # Credit score match (25%)
    if enterprise.credit_score >= region.credit_require:
        score += 25.0
    elif enterprise.credit_score >= region.credit_require * 0.8:
        score += 15.0

    # Enterprise score level (25%)
    score += min(25.0, enterprise.total_score / 40.0)

    # Province match (20%)
    if enterprise.province and enterprise.province == region.province:
        score += 20.0
    elif enterprise.province and enterprise.city and enterprise.city == region.city:
        score += 20.0
    else:
        score += 5.0

    return round(min(100.0, score), 1)

@router.get("", summary="区域需求列表")
async def list_regions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    province: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Region).where(Region.is_deleted == False, Region.status == 1)
    if province:
        query = query.where(Region.province == province)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar()
    regions = (await db.execute(
        query.offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()
    return {"total": total, "items": [RegionOut.from_orm(r) for r in regions]}

@router.post("", summary="创建区域需求", status_code=201)
async def create_region(
    data: RegionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    region = Region(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        **data.model_dump(exclude_none=True)
    )
    db.add(region)
    await db.commit()
    return RegionOut.from_orm(region)

@router.get("/{region_id}/match", summary="企业-区域匹配计算")
async def match_enterprise_region(
    region_id: str,
    enterprise_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    region = (await db.execute(
        select(Region).where(Region.id == region_id, Region.is_deleted == False)
    )).scalar_one_or_none()
    if not region:
        raise HTTPException(status_code=404, detail="区域需求不存在")

    ent = (await db.execute(
        select(Enterprise).where(Enterprise.id == enterprise_id, Enterprise.is_deleted == False)
    )).scalar_one_or_none()
    if not ent:
        raise HTTPException(status_code=404, detail="企业不存在")

    score = _compute_match_score(ent, region)
    grade = "S" if score >= 85 else "A" if score >= 70 else "B" if score >= 55 else "C" if score >= 40 else "D"

    return {
        "enterprise_id": ent.id,
        "enterprise_name": ent.name,
        "region_id": region.id,
        "region_name": region.name,
        "match_score": score,
        "match_grade": grade,
        "recommendation": grade in ("S", "A")
    }

@router.get("/{region_id}/top-enterprises", summary="区域匹配企业TOP列表")
async def top_matched_enterprises(
    region_id: str,
    top_n: int = Query(10, ge=1, le=50),
    min_score: float = Query(0.0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    region = (await db.execute(
        select(Region).where(Region.id == region_id, Region.is_deleted == False)
    )).scalar_one_or_none()
    if not region:
        raise HTTPException(status_code=404, detail="区域需求不存在")

    enterprises = (await db.execute(
        select(Enterprise).where(Enterprise.is_deleted == False, Enterprise.status == 1)
    )).scalars().all()

    results = []
    for ent in enterprises:
        ms = _compute_match_score(ent, region)
        if ms >= min_score:
            results.append({"enterprise": {"id": ent.id, "name": ent.name, "industry": ent.industry,
                                            "total_score": ent.total_score},
                             "match_score": ms})

    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results[:top_n]
