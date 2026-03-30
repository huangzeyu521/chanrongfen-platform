from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ...core.database import get_db
from ...models.enterprise import Enterprise
from ...models.expert import Expert
from ...models.docking import Docking
from ...models.user import User
from ...models.member_contribution import MemberContribution
from ..deps import get_current_user

router = APIRouter(prefix="/dashboard", tags=["数据看板"])

@router.get("/overview", summary="看板总览数据")
async def overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    total_ent = (await db.execute(
        select(func.count()).select_from(Enterprise).where(Enterprise.is_deleted == False)
    )).scalar()
    total_expert = (await db.execute(
        select(func.count()).select_from(Expert).where(Expert.is_deleted == False)
    )).scalar()
    total_docking = (await db.execute(
        select(func.count()).select_from(Docking)
    )).scalar()
    completed_docking = (await db.execute(
        select(func.count()).select_from(Docking).where(Docking.status == "completed")
    )).scalar()
    total_user = (await db.execute(
        select(func.count()).select_from(User).where(User.is_deleted == False)
    )).scalar()

    avg_score_result = (await db.execute(
        select(func.avg(Enterprise.total_score)).where(
            Enterprise.is_deleted == False, Enterprise.total_score > 0
        )
    )).scalar()

    success_rate = round(completed_docking / total_docking * 100, 1) if total_docking > 0 else 0

    return {
        "total_enterprises": total_ent,
        "total_experts": total_expert,
        "total_users": total_user,
        "total_dockings": total_docking,
        "completed_dockings": completed_docking,
        "docking_success_rate": success_rate,
        "avg_enterprise_score": round(avg_score_result or 0, 1),
    }

@router.get("/score-distribution", summary="企业评分分布")
async def score_distribution(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    enterprises = (await db.execute(
        select(Enterprise.total_score).where(
            Enterprise.is_deleted == False, Enterprise.status == 1
        )
    )).scalars().all()

    buckets = {"0-200": 0, "201-400": 0, "401-600": 0, "601-800": 0, "801-1000": 0}
    for s in enterprises:
        if s <= 200: buckets["0-200"] += 1
        elif s <= 400: buckets["201-400"] += 1
        elif s <= 600: buckets["401-600"] += 1
        elif s <= 800: buckets["601-800"] += 1
        else: buckets["801-1000"] += 1

    return [{"range": k, "count": v} for k, v in buckets.items()]

@router.get("/docking-trends", summary="对接趋势数据")
async def docking_trends(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dockings = (await db.execute(
        select(Docking.created_at, Docking.status)
    )).all()

    from collections import defaultdict
    monthly = defaultdict(lambda: {"total": 0, "completed": 0})
    for created_at, status in dockings:
        if created_at:
            key = created_at.strftime("%Y-%m")
            monthly[key]["total"] += 1
            if status == "completed":
                monthly[key]["completed"] += 1

    return [
        {"month": k, "total": v["total"], "completed": v["completed"]}
        for k, v in sorted(monthly.items())[-12:]
    ]

@router.get("/top-enterprises", summary="企业评分TOP榜")
async def top_enterprises(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ents = (await db.execute(
        select(Enterprise).where(
            Enterprise.is_deleted == False, Enterprise.status == 1, Enterprise.total_score > 0
        ).order_by(Enterprise.total_score.desc()).limit(10)
    )).scalars().all()

    return [{"rank": i+1, "id": e.id, "name": e.name,
             "industry": e.industry, "total_score": e.total_score}
            for i, e in enumerate(ents)]
