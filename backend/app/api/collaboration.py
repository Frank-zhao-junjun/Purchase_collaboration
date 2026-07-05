"""预测、产能响应、要货计划协同 API — US-301~306"""
import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.supply_chain import (
    PurchaseForecast,
    ForecastResponse,
    DeliverySchedule,
    PurchaseOrder,
    Supplier,
    ForecastStatus,
)

router = APIRouter(prefix="/collaboration", tags=["预测与要货协同"])


class ForecastCreate(BaseModel):
    supplier_id: int
    forecast_period: str = Field(..., description="如 2026Q2 / 2026年4月")
    period_start: datetime
    period_end: datetime
    items_data: List[dict] = Field(default_factory=list)


class ForecastOut(BaseModel):
    id: int
    supplier_id: int
    supplier_name: Optional[str] = None
    forecast_period: str
    period_start: datetime
    period_end: datetime
    items_data: List[dict]
    status: str
    created_at: datetime
    published_at: Optional[datetime] = None


class ForecastResponseIn(BaseModel):
    supplier_id: int
    response_data: List[dict] = Field(default_factory=list)
    risk_summary: Optional[str] = None


class DeliveryScheduleCreate(BaseModel):
    po_id: int
    supplier_id: int
    schedule_type: str = "weekly"
    required_date: datetime
    items_data: List[dict] = Field(default_factory=list)


class DeliveryScheduleOut(BaseModel):
    id: int
    po_id: int
    supplier_id: int
    supplier_name: Optional[str] = None
    schedule_type: str
    required_date: datetime
    items_data: List[dict]
    status: str
    supplier_confirmed: int
    confirmed_at: Optional[datetime] = None
    created_at: datetime


class DeliveryConfirmIn(BaseModel):
    supplier_id: int
    confirmed: bool = True
    adjustment_notes: Optional[str] = None


def _forecast_row(f: PurchaseForecast, name: Optional[str] = None) -> dict:
    try:
        items = json.loads(f.items_data or "[]")
    except json.JSONDecodeError:
        items = []
    return {
        "id": f.id,
        "supplier_id": f.supplier_id,
        "supplier_name": name,
        "forecast_period": f.forecast_period,
        "period_start": f.period_start,
        "period_end": f.period_end,
        "items_data": items,
        "status": f.status.value if hasattr(f.status, "value") else str(f.status),
        "created_at": f.created_at,
        "published_at": f.published_at,
    }


@router.get("/forecasts", response_model=List[ForecastOut])
async def list_forecasts(
    status: Optional[str] = Query(None),
    supplier_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """US-301-2 / US-302-2：列表（采购方看全部，供应商按 supplier_id 过滤）"""
    q = select(PurchaseForecast).options(selectinload(PurchaseForecast.supplier)).order_by(
        desc(PurchaseForecast.created_at)
    )
    if status:
        q = q.where(PurchaseForecast.status == ForecastStatus(status))
    if supplier_id is not None:
        q = q.where(PurchaseForecast.supplier_id == supplier_id)
    rows = (await db.execute(q)).scalars().all()
    return [
        _forecast_row(f, f.supplier.name if f.supplier else None)
        for f in rows
    ]


@router.post("/forecasts", response_model=ForecastOut)
async def create_forecast(body: ForecastCreate, db: AsyncSession = Depends(get_db)):
    """US-301-1：采购方创建预测（草稿）"""
    sup = await db.execute(select(Supplier).where(Supplier.id == body.supplier_id))
    if not sup.scalar_one_or_none():
        raise HTTPException(404, "供应商不存在")
    f = PurchaseForecast(
        supplier_id=body.supplier_id,
        forecast_period=body.forecast_period,
        period_start=body.period_start,
        period_end=body.period_end,
        items_data=json.dumps(body.items_data, ensure_ascii=False),
        status=ForecastStatus.DRAFT,
    )
    db.add(f)
    await db.commit()
    await db.refresh(f)
    r2 = await db.execute(
        select(PurchaseForecast)
        .options(selectinload(PurchaseForecast.supplier))
        .where(PurchaseForecast.id == f.id)
    )
    f2 = r2.scalar_one()
    return _forecast_row(f2, f2.supplier.name if f2.supplier else None)


@router.get("/forecasts/{forecast_id}", response_model=ForecastOut)
async def get_forecast(forecast_id: int, db: AsyncSession = Depends(get_db)):
    r = await db.execute(
        select(PurchaseForecast)
        .options(selectinload(PurchaseForecast.supplier))
        .where(PurchaseForecast.id == forecast_id)
    )
    f = r.scalar_one_or_none()
    if not f:
        raise HTTPException(404, "预测不存在")
    return _forecast_row(f, f.supplier.name if f.supplier else None)


@router.post("/forecasts/{forecast_id}/publish", response_model=ForecastOut)
async def publish_forecast(forecast_id: int, db: AsyncSession = Depends(get_db)):
    """US-301-1：发布预测，供应商可见"""
    r = await db.execute(select(PurchaseForecast).where(PurchaseForecast.id == forecast_id))
    f = r.scalar_one_or_none()
    if not f:
        raise HTTPException(404, "预测不存在")
    f.status = ForecastStatus.PUBLISHED
    f.published_at = datetime.utcnow()
    await db.commit()
    r2 = await db.execute(
        select(PurchaseForecast)
        .options(selectinload(PurchaseForecast.supplier))
        .where(PurchaseForecast.id == forecast_id)
    )
    f2 = r2.scalar_one()
    return _forecast_row(f2, f2.supplier.name if f2.supplier else None)


@router.post("/forecasts/{forecast_id}/responses")
async def submit_forecast_response(
    forecast_id: int,
    body: ForecastResponseIn,
    db: AsyncSession = Depends(get_db),
):
    """US-302-1：供应商提交产能响应"""
    r = await db.execute(select(PurchaseForecast).where(PurchaseForecast.id == forecast_id))
    fc = r.scalar_one_or_none()
    if not fc:
        raise HTTPException(404, "预测不存在")
    if fc.status != ForecastStatus.PUBLISHED:
        raise HTTPException(400, "仅已发布的预测可响应")
    if fc.supplier_id != body.supplier_id:
        raise HTTPException(400, "供应商与预测对象不一致")
    resp = ForecastResponse(
        forecast_id=forecast_id,
        supplier_id=body.supplier_id,
        response_data=json.dumps(body.response_data, ensure_ascii=False),
        risk_summary=body.risk_summary or "",
    )
    db.add(resp)
    await db.flush()
    rid = resp.id
    await db.commit()
    return {"success": True, "response_id": rid}


@router.get("/forecasts/{forecast_id}/responses")
async def list_forecast_responses(forecast_id: int, db: AsyncSession = Depends(get_db)):
    """US-302-2：采购方查看产能响应"""
    r = await db.execute(
        select(ForecastResponse).where(ForecastResponse.forecast_id == forecast_id)
    )
    out = []
    for x in r.scalars().all():
        try:
            rd = json.loads(x.response_data or "[]")
        except json.JSONDecodeError:
            rd = []
        out.append({
            "id": x.id,
            "supplier_id": x.supplier_id,
            "response_data": rd,
            "risk_summary": x.risk_summary,
            "created_at": x.created_at,
        })
    return out


def _schedule_row(s: DeliverySchedule) -> dict:
    try:
        items = json.loads(s.items_data or "[]")
    except json.JSONDecodeError:
        items = []
    return {
        "id": s.id,
        "po_id": s.po_id,
        "supplier_id": s.supplier_id,
        "supplier_name": s.supplier.name if s.supplier else None,
        "schedule_type": s.schedule_type,
        "required_date": s.required_date,
        "items_data": items,
        "status": s.status,
        "supplier_confirmed": s.supplier_confirmed,
        "confirmed_at": s.confirmed_at,
        "created_at": s.created_at,
    }


@router.get("/delivery-schedules", response_model=List[DeliveryScheduleOut])
async def list_delivery_schedules(
    supplier_id: Optional[int] = Query(None),
    po_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """US-305-2 / US-306-2"""
    q = select(DeliverySchedule).options(selectinload(DeliverySchedule.supplier)).order_by(
        desc(DeliverySchedule.created_at)
    )
    if supplier_id is not None:
        q = q.where(DeliverySchedule.supplier_id == supplier_id)
    if po_id is not None:
        q = q.where(DeliverySchedule.po_id == po_id)
    rows = (await db.execute(q)).scalars().all()
    return [_schedule_row(s) for s in rows]


@router.post("/delivery-schedules", response_model=DeliveryScheduleOut)
async def create_delivery_schedule(body: DeliveryScheduleCreate, db: AsyncSession = Depends(get_db)):
    """US-305-1：根据采购订单发布要货计划"""
    po = await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == body.po_id))
    order = po.scalar_one_or_none()
    if not order:
        raise HTTPException(404, "采购订单不存在")
    if order.supplier_id != body.supplier_id:
        raise HTTPException(400, "订单与供应商不匹配")
    s = DeliverySchedule(
        po_id=body.po_id,
        supplier_id=body.supplier_id,
        schedule_type=body.schedule_type,
        required_date=body.required_date,
        items_data=json.dumps(body.items_data, ensure_ascii=False),
        status="pending",
    )
    db.add(s)
    await db.commit()
    await db.refresh(s)
    r2 = await db.execute(
        select(DeliverySchedule)
        .options(selectinload(DeliverySchedule.supplier))
        .where(DeliverySchedule.id == s.id)
    )
    return _schedule_row(r2.scalar_one())


@router.post("/delivery-schedules/{schedule_id}/supplier-confirm", response_model=DeliveryScheduleOut)
async def supplier_confirm_schedule(
    schedule_id: int,
    body: DeliveryConfirmIn,
    db: AsyncSession = Depends(get_db),
):
    """US-306-1：供应商确认/调整建议"""
    r = await db.execute(
        select(DeliverySchedule)
        .options(selectinload(DeliverySchedule.supplier))
        .where(DeliverySchedule.id == schedule_id)
    )
    s = r.scalar_one_or_none()
    if not s:
        raise HTTPException(404, "要货计划不存在")
    if s.supplier_id != body.supplier_id:
        raise HTTPException(400, "供应商不匹配")
    s.supplier_confirmed = 1 if body.confirmed else 0
    s.confirmed_at = datetime.utcnow()
    if body.adjustment_notes:
        s.status = "adjusted"
        cur = json.loads(s.items_data or "[]")
        if isinstance(cur, list):
            cur.append({"type": "adjustment_note", "text": body.adjustment_notes})
            s.items_data = json.dumps(cur, ensure_ascii=False)
    else:
        s.status = "confirmed"
    await db.commit()
    await db.refresh(s)
    r2 = await db.execute(
        select(DeliverySchedule)
        .options(selectinload(DeliverySchedule.supplier))
        .where(DeliverySchedule.id == schedule_id)
    )
    return _schedule_row(r2.scalar_one())
