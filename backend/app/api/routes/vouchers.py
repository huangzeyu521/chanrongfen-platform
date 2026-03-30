import os, uuid, shutil
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...core.database import get_db
from ...models.voucher import Voucher
from ..deps import get_current_user, require_admin
from ...models.user import User
from ...core.config import settings

router = APIRouter(prefix="/vouchers", tags=["凭证管理"])

ALLOWED_TYPES = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx", ".xls", ".xlsx"}

@router.post("", summary="上传凭证文件", status_code=201)
async def upload_voucher(
    entity_type: str = Form(...),
    entity_id: str = Form(...),
    score_dim: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Validate file type
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_TYPES:
        raise HTTPException(status_code=422, detail=f"不支持的文件类型，允许：{ALLOWED_TYPES}")

    # Validate file size
    content = await file.read()
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=422, detail=f"文件超过大小限制 {settings.MAX_FILE_SIZE_MB}MB")

    # Save file
    upload_dir = os.path.join(settings.UPLOAD_DIR, entity_type, entity_id)
    os.makedirs(upload_dir, exist_ok=True)
    file_id = str(uuid.uuid4())
    save_path = os.path.join(upload_dir, f"{file_id}{ext}")

    with open(save_path, "wb") as f:
        f.write(content)

    voucher = Voucher(
        id=file_id,
        entity_type=entity_type,
        entity_id=entity_id,
        score_dim=score_dim,
        file_name=file.filename,
        file_path=save_path,
        file_size=len(content),
        file_type=ext.lstrip("."),
        status=0,
        uploaded_by=current_user.id
    )
    db.add(voucher)
    await db.commit()
    return {"id": voucher.id, "file_name": voucher.file_name, "status": "pending_review"}

@router.get("", summary="凭证列表")
async def list_vouchers(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    status: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Voucher)
    if entity_type:
        query = query.where(Voucher.entity_type == entity_type)
    if entity_id:
        query = query.where(Voucher.entity_id == entity_id)
    if status is not None:
        query = query.where(Voucher.status == status)

    vouchers = (await db.execute(query.order_by(Voucher.created_at.desc()))).scalars().all()
    return [
        {
            "id": v.id, "entity_type": v.entity_type, "entity_id": v.entity_id,
            "score_dim": v.score_dim, "file_name": v.file_name,
            "file_size": v.file_size, "status": v.status,
            "review_comment": v.review_comment,
            "created_at": v.created_at.isoformat() if v.created_at else None
        }
        for v in vouchers
    ]

@router.patch("/{voucher_id}/review", summary="审核凭证")
async def review_voucher(
    voucher_id: str,
    status: int = Form(...),    # 1=approved, 2=rejected
    comment: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    v = (await db.execute(
        select(Voucher).where(Voucher.id == voucher_id)
    )).scalar_one_or_none()
    if not v:
        raise HTTPException(status_code=404, detail="凭证不存在")
    if status not in (1, 2):
        raise HTTPException(status_code=422, detail="审核状态无效 (1=通过, 2=拒绝)")

    v.status = status
    v.review_comment = comment
    v.reviewer_id = current_user.id
    v.reviewed_at = datetime.utcnow()
    await db.commit()
    return {"message": "审核完成", "status": status}
