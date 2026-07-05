"""物流与入库管理 API - ASN/运单/入库"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from sqlalchemy.orm import selectinload
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

from app.core.database import get_db
from app.models.supply_chain import ASN, ShipmentNote, ShipmentNoteItem, Receipt, ReceiptItem, Warehouse, PurchaseOrder, ShipmentStatus

router = APIRouter(prefix="/logistics", tags=["物流与入库"])


# ==================== Schemas ====================

class ShipmentNoteResponse(BaseModel):
    id: int
    shipment_no: str
    purchase_order_id: int
    supplier_id: int
    supplier_name: Optional[str] = None
    status: str
    carrier_name: Optional[str]
    tracking_no: Optional[str]
    vehicle_no: Optional[str]
    driver_name: Optional[str]
    driver_phone: Optional[str]
    expected_arrival: Optional[datetime]
    actual_arrival: Optional[datetime]
    shipping_address: Optional[str]
    receiving_warehouse: Optional[str]
    total_quantity: float
    created_at: datetime


class ShipmentNoteCreate(BaseModel):
    purchase_order_id: int
    supplier_id: int
    carrier_name: Optional[str] = None
    tracking_no: Optional[str] = None
    vehicle_no: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    expected_arrival: Optional[str] = None
    shipping_address: Optional[str] = None
    receiving_warehouse: Optional[str] = None
    total_quantity: float = 0
    items: List[dict] = []  # [{material_name, quantity, unit}]


class ReceiptCreate(BaseModel):
    receipt_no: Optional[str] = None
    asn_id: Optional[int] = None  # 可关联 ASN
    warehouse_id: int
    supplier_id: int
    purchase_order_id: Optional[int] = None
    remarks: Optional[str] = None
    items: List[dict] = []  # [{material_id, material_name, quantity, unit, batch_no, quality_result}]


class ShipmentApproveIn(BaseModel):
    approved: bool = True
    reason: Optional[str] = None


class PackingListIn(BaseModel):
    items: List[dict] = []  # [{material_name, quantity, batch_no, production_date, package_count, notes}]


class ReceiptResponse(BaseModel):
    id: int
    receipt_no: str
    warehouse_id: int
    warehouse_name: Optional[str] = None
    supplier_id: int
    supplier_name: Optional[str] = None
    purchase_order_id: Optional[int]
    status: str
    total_quantity: float
    qualified_quantity: float
    unqualified_quantity: float
    inspector: Optional[str]
    inspected_at: Optional[datetime]
    remarks: Optional[str]
    items: List[dict]
    created_at: datetime
    updated_at: datetime


# ==================== ASN/运单接口 ====================

@router.get("/shipment-notes/", response_model=List[ShipmentNoteResponse])
async def list_shipment_notes(
    status: Optional[str] = Query(None, description="状态筛选"),
    supplier_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """获取运单列表"""
    from app.models.supply_chain import Supplier
    
    query = select(ShipmentNote).options(selectinload(ShipmentNote.supplier))
    
    if status:
        query = query.where(ShipmentNote.status == status)
    if supplier_id:
        query = query.where(ShipmentNote.supplier_id == supplier_id)
    
    query = query.order_by(desc(ShipmentNote.created_at))
    
    result = await db.execute(query)
    notes = result.scalars().all()
    
    return [_format_shipment_note(n) for n in notes]


@router.post("/shipment-notes/", response_model=ShipmentNoteResponse)
async def create_shipment_note(
    body: ShipmentNoteCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建运单/ASN (供应商创建送货计划)"""
    import uuid
    shipment_no = f"SN{datetime.utcnow().strftime('%Y%m%d')}{str(uuid.uuid4())[:6].upper()}"

    note = ShipmentNote(
        shipment_no=shipment_no,
        purchase_order_id=body.purchase_order_id,
        supplier_id=body.supplier_id,
        status=ShipmentStatus.DRAFT,
        carrier_name=body.carrier_name,
        tracking_no=body.tracking_no,
        vehicle_no=body.vehicle_no,
        driver_name=body.driver_name,
        driver_phone=body.driver_phone,
        expected_arrival=datetime.strptime(body.expected_arrival, "%Y-%m-%d") if body.expected_arrival else None,
        shipping_address=body.shipping_address,
        receiving_warehouse=body.receiving_warehouse,
        total_quantity=body.total_quantity,
    )
    db.add(note)
    await db.flush()
    await db.refresh(note)

    # 创建运单明细
    for item_data in body.items:
        item = ShipmentNoteItem(
            shipment_note_id=note.id,
            material_id=item_data.get("material_id") or 1,
            material_name=item_data.get("material_name", ""),
            quantity=item_data.get("quantity", 0),
            unit=item_data.get("unit", "吨"),
            batch_no=item_data.get("batch_no"),
        )
        db.add(item)

    await db.commit()
    # 重新查询以加载关系
    result = await db.execute(
        select(ShipmentNote)
        .options(selectinload(ShipmentNote.supplier))
        .where(ShipmentNote.id == note.id)
    )
    note = result.scalar_one()
    return _format_shipment_note(note)


@router.get("/shipment-notes/{note_id}", response_model=ShipmentNoteResponse)
async def get_shipment_note(
    note_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取运单详情"""
    result = await db.execute(
        select(ShipmentNote).options(selectinload(ShipmentNote.supplier)).where(ShipmentNote.id == note_id)
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="运单不存在")
    return _format_shipment_note(note)


@router.get("/shipment-notes/{note_id}/items")
async def get_shipment_note_items(
    note_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取运单货物明细"""
    result = await db.execute(
        select(ShipmentNoteItem).where(ShipmentNoteItem.shipment_note_id == note_id)
    )
    items = result.scalars().all()
    return [
        {
            "id": item.id,
            "material_name": item.material_name,
            "quantity": item.quantity,
            "unit": item.unit,
            "batch_no": item.batch_no,
            "production_date": item.production_date,
            "origin_location": item.origin_location,
            "quality_grade": item.quality_grade,
            "package_count": item.package_count,
        }
        for item in items
    ]


@router.post("/shipment-notes/{note_id}/arrive")
async def confirm_arrival(
    note_id: int,
    db: AsyncSession = Depends(get_db)
):
    """确认到货（入库员操作）"""
    result = await db.execute(
        select(ShipmentNote).where(ShipmentNote.id == note_id)
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="运单不存在")
    
    note.status = "arrived"
    note.actual_arrival = datetime.utcnow()
    await db.commit()

    return {"success": True, "message": "已确认到货"}


@router.post("/shipment-notes/{note_id}/submit")
async def submit_shipment_note(
    note_id: int,
    db: AsyncSession = Depends(get_db)
):
    """US-307/308：供应商提交送货计划"""
    result = await db.execute(
        select(ShipmentNote).where(ShipmentNote.id == note_id)
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="运单不存在")

    current = note.status.value if hasattr(note.status, "value") else str(note.status)
    if current == ShipmentStatus.SUBMITTED.value:
        return {"success": True, "message": "送货计划已提交", "status": current}
    if current not in (ShipmentStatus.DRAFT.value, ShipmentStatus.REJECTED.value):
        raise HTTPException(status_code=400, detail=f"当前状态 {current} 不可提交")

    note.status = ShipmentStatus.SUBMITTED
    await db.commit()
    return {"success": True, "message": "送货计划已提交", "status": ShipmentStatus.SUBMITTED.value}


# ==================== US-308: 采购方确认/拒绝送货计划 ====================

@router.post("/shipment-notes/{note_id}/approve")
async def approve_shipment_note(
    note_id: int,
    body: ShipmentApproveIn = Body(default_factory=ShipmentApproveIn),
    db: AsyncSession = Depends(get_db)
):
    """US-308-1：采购方批准或拒绝送货计划"""
    result = await db.execute(
        select(ShipmentNote).where(ShipmentNote.id == note_id)
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="运单不存在")

    if body.approved:
        note.status = ShipmentStatus.APPROVED
        msg = "送货计划已批准"
    else:
        note.status = ShipmentStatus.REJECTED
        note.notes = (note.notes or "") + f"\n[拒绝原因] {body.reason or '未提供'}"
        msg = "送货计划已拒绝"

    await db.commit()
    return {"success": True, "message": msg, "status": note.status.value if hasattr(note.status, "value") else str(note.status)}


@router.post("/shipment-notes/{note_id}/reject")
async def reject_shipment_note(
    note_id: int,
    reason: str = Query("采购方拒绝"),
    db: AsyncSession = Depends(get_db)
):
    """US-308-1：采购方拒绝送货计划（快捷入口）"""
    return await approve_shipment_note(
        note_id,
        ShipmentApproveIn(approved=False, reason=reason),
        db,
    )


# ==================== US-309: 装箱单与批次信息 ====================

@router.post("/shipment-notes/{note_id}/packing-list")
async def submit_packing_list(
    note_id: int,
    body: PackingListIn,
    db: AsyncSession = Depends(get_db)
):
    """US-309-1：供应商提交装箱单与批次信息"""
    result = await db.execute(
        select(ShipmentNote).options(selectinload(ShipmentNote.items)).where(ShipmentNote.id == note_id)
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="运单不存在")

    # 更新运单明细的批次和装箱信息
    existing = {item.id: item for item in note.items}
    for packing_item in body.items:
        item_id = packing_item.get("id")
        if item_id and item_id in existing:
            item = existing[item_id]
            item.batch_no = packing_item.get("batch_no", item.batch_no)
            item.production_date = packing_item.get("production_date", item.production_date)
            item.package_count = packing_item.get("package_count", item.package_count)
            item.notes = packing_item.get("notes", item.notes)
        else:
            prod = packing_item.get("production_date")
            prod_dt = None
            if prod:
                try:
                    prod_dt = datetime.fromisoformat(str(prod).replace("Z", ""))
                except ValueError:
                    prod_dt = None
            new_item = ShipmentNoteItem(
                shipment_note_id=note.id,
                material_id=packing_item.get("material_id") or 1,
                material_name=packing_item.get("material_name", ""),
                quantity=packing_item.get("quantity", 0),
                unit=packing_item.get("unit", "吨"),
                batch_no=packing_item.get("batch_no", ""),
                production_date=prod_dt,
                package_count=packing_item.get("package_count", 1),
                notes=packing_item.get("notes", ""),
            )
            db.add(new_item)

    await db.commit()
    return {"success": True, "message": "装箱单与批次信息已提交"}


@router.post("/shipment-notes/{note_id}/packing-lists")
async def submit_packing_lists(
    note_id: int,
    body: PackingListIn,
    db: AsyncSession = Depends(get_db)
):
    """US-309-1：烟测路径别名（复数 packing-lists）"""
    return await submit_packing_list(note_id, body, db)


@router.get("/shipment-notes/{note_id}/packing-list")
async def get_packing_list(
    note_id: int,
    db: AsyncSession = Depends(get_db)
):
    """US-309-2：查看装箱单与批次信息"""
    result = await db.execute(
        select(ShipmentNoteItem).where(ShipmentNoteItem.shipment_note_id == note_id)
    )
    items = result.scalars().all()
    return [
        {
            "id": item.id,
            "material_name": item.material_name,
            "quantity": item.quantity,
            "unit": item.unit,
            "batch_no": item.batch_no,
            "production_date": item.production_date.isoformat() if item.production_date else None,
            "origin_location": item.origin_location,
            "quality_grade": item.quality_grade,
            "package_count": item.package_count,
            "notes": item.notes,
        }
        for item in items
    ]


@router.get("/shipment-notes/{note_id}/packing-lists")
async def get_packing_lists(
    note_id: int,
    db: AsyncSession = Depends(get_db)
):
    """US-309-2：烟测路径别名（复数 packing-lists）"""
    return await get_packing_list(note_id, db)


# ==================== 入库单接口 ====================

@router.get("/receipts/", response_model=List[ReceiptResponse])
async def list_receipts(
    status: Optional[str] = Query(None, description="pending/qualified/unqualified"),
    warehouse_id: Optional[int] = Query(None),
    supplier_id: Optional[int] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """获取入库单列表"""
    query = select(Receipt).options(
        selectinload(Receipt.warehouse),
        selectinload(Receipt.supplier),
        selectinload(Receipt.items_rel)
    )
    
    if status:
        query = query.where(Receipt.status == status)
    if warehouse_id:
        query = query.where(Receipt.warehouse_id == warehouse_id)
    if supplier_id:
        query = query.where(Receipt.supplier_id == supplier_id)
    if keyword:
        query = query.where(Receipt.receipt_no.contains(keyword))
    
    query = query.order_by(desc(Receipt.created_at))
    
    result = await db.execute(query)
    receipts = result.scalars().all()
    
    return [_format_receipt(r) for r in receipts]


@router.get("/receipts/{receipt_id}", response_model=ReceiptResponse)
async def get_receipt(
    receipt_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取入库单详情"""
    result = await db.execute(
        select(Receipt).options(
            selectinload(Receipt.warehouse),
            selectinload(Receipt.supplier),
            selectinload(Receipt.items_rel)
        ).where(Receipt.id == receipt_id)
    )
    receipt = result.scalar_one_or_none()
    if not receipt:
        raise HTTPException(status_code=404, detail="入库单不存在")
    return _format_receipt(receipt)


@router.post("/receipts/", response_model=ReceiptResponse)
async def create_receipt(
    data: ReceiptCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建入库单（质检合格后入库）"""
    from app.models.supply_chain import Supplier, Receipt as ReceiptModel, ReceiptItem as ReceiptItemModel
    
    # 生成入库单号
    receipt_no = data.receipt_no or f"RC{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # 计算汇总数量
    total_qty = sum(item.get('quantity', 0) for item in data.items)
    qualified_qty = sum(
        item.get('quantity', 0) for item in data.items 
        if item.get('quality_result') == 'qualified'
    )
    unqualified_qty = total_qty - qualified_qty
    
    receipt = ReceiptModel(
        receipt_no=receipt_no,
        warehouse_id=data.warehouse_id,
        supplier_id=data.supplier_id,
        purchase_order_id=data.purchase_order_id,
        asn_id=data.asn_id,
        status='qualified',
        total_quantity=total_qty,
        qualified_quantity=qualified_qty,
        unqualified_quantity=unqualified_qty,
        inspector=data.remarks or '系统',
        inspected_at=datetime.utcnow(),
        remarks=data.remarks,
    )
    db.add(receipt)
    await db.flush()
    
    # 添加入库明细
    for item_data in data.items:
        item = ReceiptItemModel(
            receipt_id=receipt.id,
            material_id=item_data.get('material_id'),
            material_name=item_data.get('material_name', ''),
            quantity=item_data.get('quantity', 0),
            unit=item_data.get('unit', ''),
            batch_no=item_data.get('batch_no', ''),
            production_date=item_data.get('production_date'),
            quality_result=item_data.get('quality_result', 'qualified'),
            warehouse_location=item_data.get('warehouse_location', ''),
        )
        db.add(item)
    
    await db.commit()
    
    # 重新查询获取关联数据
    result = await db.execute(
        select(Receipt).options(
            selectinload(Receipt.warehouse),
            selectinload(Receipt.supplier),
            selectinload(Receipt.items_rel)
        ).where(Receipt.id == receipt.id)
    )
    return _format_receipt(result.scalar_one())


@router.get("/receipts/stats/summary")
async def get_receipt_stats(
    db: AsyncSession = Depends(get_db)
):
    """获取入库统计"""
    from app.models.supply_chain import Receipt as ReceiptModel
    
    # 今日入库
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_result = await db.execute(
        select(func.count(), func.sum(ReceiptModel.total_quantity))
        .where(ReceiptModel.created_at >= today_start)
    )
    today_count, today_qty = today_result.one()
    
    # 本月入库
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_result = await db.execute(
        select(func.count(), func.sum(ReceiptModel.total_quantity))
        .where(ReceiptModel.created_at >= month_start)
    )
    month_count, month_qty = month_result.one()
    
    # 待入库数量
    pending_result = await db.execute(
        select(func.count())
        .where(ShipmentNote.status.in_(['shipped', 'in_transit']))
    )
    pending_count = pending_result.scalar()
    
    return {
        "today_count": today_count or 0,
        "today_quantity": float(today_qty or 0),
        "month_count": month_count or 0,
        "month_quantity": float(month_qty or 0),
        "pending_receipt_count": pending_count or 0,
    }


# ==================== 辅助函数 ====================

def _format_shipment_note(note: ShipmentNote) -> dict:
    """格式化运单"""
    return {
        "id": note.id,
        "shipment_no": note.shipment_no,
        "purchase_order_id": note.purchase_order_id,
        "supplier_id": note.supplier_id,
        "supplier_name": note.supplier.name if note.supplier else None,
        "status": note.status.value if hasattr(note.status, "value") else str(note.status),
        "carrier_name": note.carrier_name,
        "tracking_no": note.tracking_no,
        "vehicle_no": note.vehicle_no,
        "driver_name": note.driver_name,
        "driver_phone": note.driver_phone,
        "expected_arrival": note.expected_arrival,
        "actual_arrival": note.actual_arrival,
        "shipping_address": note.shipping_address,
        "receiving_warehouse": note.receiving_warehouse,
        "total_quantity": note.total_quantity,
        "created_at": note.created_at,
    }


def _format_receipt(receipt: Receipt) -> dict:
    """格式化入库单"""
    items = []
    for item in getattr(receipt, 'items_rel', []) or []:
        items.append({
            "id": item.id,
            "material_id": item.material_id,
            "material_name": item.material_name,
            "quantity": item.quantity,
            "unit": item.unit,
            "batch_no": item.batch_no,
            "production_date": item.production_date,
            "quality_result": item.quality_result,
            "warehouse_location": item.warehouse_location,
        })
    
    return {
        "id": receipt.id,
        "receipt_no": receipt.receipt_no,
        "warehouse_id": receipt.warehouse_id,
        "warehouse_name": receipt.warehouse.name if receipt.warehouse else None,
        "supplier_id": receipt.supplier_id,
        "supplier_name": receipt.supplier.name if receipt.supplier else None,
        "purchase_order_id": receipt.purchase_order_id,
        "status": receipt.status,
        "total_quantity": receipt.total_quantity,
        "qualified_quantity": receipt.qualified_quantity,
        "unqualified_quantity": receipt.unqualified_quantity,
        "inspector": receipt.inspector,
        "inspected_at": receipt.inspected_at,
        "remarks": receipt.remarks,
        "items": items,
        "created_at": receipt.created_at,
        "updated_at": receipt.updated_at,
    }
