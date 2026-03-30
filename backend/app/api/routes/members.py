from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from ...core.database import get_db
from ...models.member_contribution import MemberContribution
from ...models.enterprise import Enterprise
from ..deps import get_current_user, require_admin
from ...models.user import User
import uuid

router = APIRouter(prefix="/members", tags=["会员贡献"])

class ContributionCreate(BaseModel):
    enterprise_id: str
    action_type: str  # fee_paid/recommend/activity/resource
    action_detail: Optional[str] = None
    score_earned: float
    action_date: str
    remark: Optional[str] = None

ACTION_TYPE_SCORES = {
    "fee_paid": {"max": 30, "base": 20},
    "recommend_member": {"max": 25, "base": 15},
    "recommend_project": {"max": 20, "base": 10},
    "join_activity": {"max": 10, "base": 5},
    "organize_activity": {"max": 20, "base": 15},
    "gov_resource": {"max": 20, "base": 15},
    "expert_service": {"max": 15, "base": 10},
}

@router.get("/{enterprise_id}/contribution", summary="获取会员贡献分")
async def get_contribution(
    enterprise_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ent = (await db.execute(
        select(Enterprise).where(Enterprise.id == enterprise_id)
    )).scalar_one_or_none()
    if not ent:
        raise HTTPException(status_code=404, detail="企业不存在")

    records = (await db.execute(
        select(MemberContribution).where(MemberContribution.enterprise_id == enterprise_id)
        .order_by(MemberContribution.created_at.desc())
    )).scalars().all()

    total = sum(r.score_earned for r in records)
    grade = _contribution_grade(total)

    return {
        "enterprise_id": enterprise_id,
        "enterprise_name": ent.name,
        "total_contribution_score": round(total, 1),
        "grade": grade,
        "rights": _get_rights(grade),
        "record_count": len(records),
        "records": [
            {
                "id": r.id,
                "action_type": r.action_type,
                "action_detail": r.action_detail,
                "score_earned": r.score_earned,
                "action_date": r.action_date.isoformat() if r.action_date else None
            }
            for r in records[:20]
        ]
    }

def _contribution_grade(score: float) -> str:
    if score >= 700: return "S"
    if score >= 500: return "A"
    if score >= 300: return "B"
    return "C"

def _get_rights(grade: str) -> dict:
    rights_map = {
        "S": {"display_weight": 1.5, "priority_award": True, "council_bonus": 20},
        "A": {"display_weight": 1.2, "priority_award": True, "council_bonus": 10},
        "B": {"display_weight": 1.0, "priority_award": False, "council_bonus": 0},
        "C": {"display_weight": 0.8, "priority_award": False, "council_bonus": 0},
    }
    return rights_map.get(grade, rights_map["C"])

@router.post("/contribution/record", summary="记录贡献行为")
async def record_contribution(
    data: ContributionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    ent = (await db.execute(
        select(Enterprise).where(Enterprise.id == data.enterprise_id)
    )).scalar_one_or_none()
    if not ent:
        raise HTTPException(status_code=404, detail="企业不存在")

    record = MemberContribution(
        id=str(uuid.uuid4()),
        enterprise_id=data.enterprise_id,
        action_type=data.action_type,
        action_detail=data.action_detail,
        score_earned=data.score_earned,
        action_date=date.fromisoformat(data.action_date),
        verified_by=current_user.id,
        remark=data.remark
    )
    db.add(record)
    await db.commit()
    return {"message": "贡献记录已保存", "id": record.id}

@router.get("/contribution/leaderboard", summary="贡献分排行榜")
async def leaderboard(
    top_n: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Aggregate contribution scores by enterprise
    records = (await db.execute(
        select(MemberContribution)
    )).scalars().all()

    score_map = {}
    for r in records:
        score_map[r.enterprise_id] = score_map.get(r.enterprise_id, 0) + r.score_earned

    # Get enterprise names
    if not score_map:
        return []

    ents = (await db.execute(
        select(Enterprise).where(Enterprise.id.in_(list(score_map.keys())))
    )).scalars().all()
    ent_map = {e.id: e.name for e in ents}

    results = [
        {"enterprise_id": eid, "enterprise_name": ent_map.get(eid, ""),
         "total_score": round(s, 1), "grade": _contribution_grade(s)}
        for eid, s in score_map.items()
    ]
    results.sort(key=lambda x: x["total_score"], reverse=True)
    return results[:top_n]
