"""公告栏 API - 公告/政策/操作指引"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from sqlalchemy.orm import selectinload
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

from app.core.database import get_db
from app.models.supply_chain import Announcement, AnnouncementRead, AnnouncementType

router = APIRouter(prefix="/announcements", tags=["公告栏"])


# ==================== Schemas ====================

class AnnouncementCreate(BaseModel):
    title: str
    content: str
    announcement_type: str = "announcement"  # announcement/policy/guide
    priority: int = 0  # 0-普通, 1-重要, 2-紧急
    is_pinned: bool = False
    attachments: Optional[List[dict]] = []
    published_by: Optional[str] = None
    valid_until: Optional[datetime] = None


class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    announcement_type: Optional[str] = None
    priority: Optional[int] = None
    is_pinned: Optional[bool] = None
    attachments: Optional[List[dict]] = None
    valid_until: Optional[datetime] = None


class AnnouncementResponse(BaseModel):
    id: int
    title: str
    content: str
    announcement_type: str
    priority: int
    is_pinned: bool
    attachments: List[dict]
    published_by: Optional[str]
    published_at: datetime
    valid_from: datetime
    valid_until: Optional[datetime]
    view_count: int
    created_at: datetime


# ==================== 采购端: 发布公告 ====================

@router.post("/", response_model=AnnouncementResponse)
async def create_announcement(
    data: AnnouncementCreate,
    db: AsyncSession = Depends(get_db)
):
    """采购端: 发布新公告"""
    now = datetime.utcnow()
    announcement = Announcement(
        title=data.title,
        content=data.content,
        announcement_type=AnnouncementType(data.announcement_type),
        priority=data.priority,
        is_pinned=1 if data.is_pinned else 0,
        attachments="[]" if not data.attachments else str(data.attachments).replace("'", '"'),
        published_by=data.published_by or "系统管理员",
        valid_from=now,
        valid_until=data.valid_until,
    )
    db.add(announcement)
    await db.commit()
    await db.refresh(announcement)
    return _format_announcement(announcement)


@router.put("/{announcement_id}", response_model=AnnouncementResponse)
async def update_announcement(
    announcement_id: int,
    data: AnnouncementUpdate,
    db: AsyncSession = Depends(get_db)
):
    """采购端: 编辑公告"""
    result = await db.execute(
        select(Announcement).where(Announcement.id == announcement_id)
    )
    announcement = result.scalar_one_or_none()
    if not announcement:
        raise HTTPException(status_code=404, detail="公告不存在")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "announcement_type" and value:
            value = AnnouncementType(value)
        elif field == "is_pinned":
            value = 1 if value else 0
        elif field == "attachments" and value:
            value = str(value).replace("'", '"')
        setattr(announcement, field, value)

    await db.commit()
    await db.refresh(announcement)
    return _format_announcement(announcement)


@router.delete("/{announcement_id}")
async def delete_announcement(
    announcement_id: int,
    db: AsyncSession = Depends(get_db)
):
    """采购端: 删除公告"""
    result = await db.execute(
        select(Announcement).where(Announcement.id == announcement_id)
    )
    announcement = result.scalar_one_or_none()
    if not announcement:
        raise HTTPException(status_code=404, detail="公告不存在")

    await db.delete(announcement)
    await db.commit()
    return {"success": True, "message": "公告已删除"}


@router.get("/")
async def list_announcements(
    announcement_type: Optional[str] = Query(None, description="筛选类型: announcement/policy/guide"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """获取公告列表（采购端和供应商端共用）"""
    query = select(Announcement)
    
    # 类型筛选
    if announcement_type:
        query = query.where(Announcement.announcement_type == AnnouncementType(announcement_type))
    
    # 关键词搜索
    if keyword:
        query = query.where(
            or_(
                Announcement.title.contains(keyword),
                Announcement.content.contains(keyword)
            )
        )
    
    # 有效期筛选（只显示有效期内公告）
    now = datetime.utcnow()
    query = query.where(
        or_(
            Announcement.valid_until.is_(None),
            Announcement.valid_until >= now
        )
    )
    
    # 统计总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页 + 排序（置顶优先，然后按发布时间倒序）
    query = query.order_by(
        desc(Announcement.is_pinned),
        desc(Announcement.priority),
        desc(Announcement.published_at)
    ).offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    announcements = result.scalars().all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_format_announcement(a) for a in announcements]
    }


@router.get("/types/summary")
async def get_announcement_types_summary(
    db: AsyncSession = Depends(get_db)
):
    """获取各类型公告数量统计"""
    now = datetime.utcnow()
    results = []

    for ann_type in AnnouncementType:
        query = select(func.count()).select_from(Announcement).where(
            Announcement.announcement_type == ann_type,
            or_(
                Announcement.valid_until.is_(None),
                Announcement.valid_until >= now
            )
        )
        result = await db.execute(query)
        count = result.scalar()
        results.append({
            "type": ann_type.value,
            "label": _get_type_label(ann_type.value),
            "count": count
        })

    return results


@router.get("/{announcement_id}", response_model=AnnouncementResponse)
async def get_announcement(
    announcement_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取公告详情（采购端和供应商端共用）"""
    result = await db.execute(
        select(Announcement).where(Announcement.id == announcement_id)
    )
    announcement = result.scalar_one_or_none()
    if not announcement:
        raise HTTPException(status_code=404, detail="公告不存在")
    
    # 增加阅读次数
    announcement.view_count = (announcement.view_count or 0) + 1
    await db.commit()
    
    return _format_announcement(announcement)


@router.post("/{announcement_id}/record-read")
async def record_announcement_read(
    announcement_id: int,
    user_id: int = Query(..., description="用户ID"),
    db: AsyncSession = Depends(get_db)
):
    """记录用户阅读公告（供应商端调用）"""
    result = await db.execute(
        select(Announcement).where(Announcement.id == announcement_id)
    )
    announcement = result.scalar_one_or_none()
    if not announcement:
        raise HTTPException(status_code=404, detail="公告不存在")
    
    # 检查是否已阅读
    check = await db.execute(
        select(AnnouncementRead)
        .where(AnnouncementRead.announcement_id == announcement_id)
        .where(AnnouncementRead.user_id == user_id)
    )
    existing = check.scalar_one_or_none()
    
    if not existing:
        read_record = AnnouncementRead(
            announcement_id=announcement_id,
            user_id=user_id
        )
        db.add(read_record)
        await db.commit()
    
    return {"success": True, "message": "已记录阅读"}


# ==================== 辅助函数 ====================

def _format_announcement(a: Announcement) -> dict:
    """格式化公告响应"""
    import json
    attachments = []
    try:
        attachments = json.loads(a.attachments) if a.attachments else []
    except:
        pass
    
    return {
        "id": a.id,
        "title": a.title,
        "content": a.content,
        "announcement_type": a.announcement_type.value if isinstance(a.announcement_type, AnnouncementType) else a.announcement_type,
        "priority": a.priority,
        "is_pinned": bool(a.is_pinned),
        "attachments": attachments,
        "published_by": a.published_by,
        "published_at": a.published_at,
        "valid_from": a.valid_from,
        "valid_until": a.valid_until,
        "view_count": a.view_count or 0,
        "created_at": a.created_at,
    }


def _get_type_label(ann_type: str) -> str:
    """获取类型标签"""
    labels = {
        "announcement": "公告",
        "policy": "政策",
        "guide": "操作指引"
    }
    return labels.get(ann_type, ann_type)
