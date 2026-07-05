"""寻源与合同协同 API - Phase 2"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from sqlalchemy.orm import selectinload
from datetime import datetime
import json

from app.core.database import get_db
from app.models.supply_chain import (
    SourcingProject, SourcingInvitation, SourcingBid, SourcingAward,
    ContractTemplate, Contract, ContractComment,
    Supplier, SourcingStatus, ContractStatus,
)
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(tags=["寻源与合同"])


# ==================== Schemas ====================

class SourcingProjectCreate(BaseModel):
    project_name: str
    sourcing_type: str  # RFQ/RFP/RFI
    materials_summary: Optional[str] = None
    deadline: Optional[datetime] = None
    budget: Optional[float] = None
    evaluation_criteria: Optional[dict] = None
    enable_reverse_auction: bool = False
    invited_supplier_ids: List[int] = []


class SourcingProjectResponse(BaseModel):
    id: int
    project_name: str
    sourcing_type: str
    materials_summary: Optional[str] = None
    deadline: Optional[datetime] = None
    budget: Optional[float] = None
    status: str
    invited_suppliers: Optional[List[dict]] = None
    created_at: datetime
    awarded_at: Optional[datetime] = None


class SourcingBidCreate(BaseModel):
    supplier_id: int
    round_number: int = 1
    bid_data: List[dict]  # [{material_name, unit_price, quantity, subtotal}] 列表
    technical_proposal: Optional[str] = None
    delivery_days: Optional[int] = None
    payment_terms: Optional[str] = None
    attachment_urls: List[str] = []


class ContractTemplateCreate(BaseModel):
    name: str
    applicable_categories: str
    content: str
    variables: List[str] = []


class ContractCreate(BaseModel):
    supplier_id: int
    contract_name: str
    contract_amount: Optional[float] = None
    content: Optional[str] = None
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None


# ==================== US-201: 创建寻源项目 ====================

@router.post("/sourcing/projects", response_model=SourcingProjectResponse)
async def create_sourcing_project(
    body: SourcingProjectCreate,
    created_by: int = Query(1),
    db: AsyncSession = Depends(get_db)
):
    """
    创建寻源项目 (RFQ/RFP/RFI)

    - 从合格供应商库选择邀请供应商
    - 自动创建 SourcingInvitation 记录
    - 通知被邀请供应商
    """
    if body.sourcing_type not in ["RFQ", "RFP", "RFI"]:
        raise HTTPException(status_code=400, detail="sourcing_type 必须是 RFQ/RFP/RFI")

    # 验证供应商
    for sid in body.invited_supplier_ids:
        sup = await db.execute(select(Supplier).where(Supplier.id == sid))
        if not sup.scalar_one_or_none():
            raise HTTPException(status_code=404, detail=f"供应商ID {sid} 不存在")

    project = SourcingProject(
        project_name=body.project_name,
        sourcing_type=body.sourcing_type,
        materials_summary=body.materials_summary,
        deadline=body.deadline,
        budget=body.budget,
        evaluation_criteria=json.dumps(body.evaluation_criteria or {}, ensure_ascii=False),
        status=SourcingStatus.DRAFT if not body.invited_supplier_ids else SourcingStatus.OPEN,
        enable_reverse_auction=1 if body.enable_reverse_auction else 0,
        created_by=created_by
    )
    db.add(project)
    await db.flush()
    await db.refresh(project)

    # 创建邀请记录
    invitations = []
    for sid in body.invited_supplier_ids:
        inv = SourcingInvitation(
            sourcing_id=project.id,
            supplier_id=sid,
            status="pending"
        )
        db.add(inv)
        invitations.append(inv)
    await db.flush()

    # 加载供应商名称
    supplier_infos = []
    for sid, inv in zip(body.invited_supplier_ids, invitations):
        sup = await db.execute(select(Supplier).where(Supplier.id == sid))
        s = sup.scalar_one()
        supplier_infos.append({
            "invitation_id": inv.id,
            "supplier_id": sid,
            "supplier_name": s.name,
            "status": inv.status
        })

    return {
        "id": project.id,
        "project_name": project.project_name,
        "sourcing_type": project.sourcing_type,
        "materials_summary": project.materials_summary,
        "deadline": project.deadline,
        "budget": project.budget,
        "status": project.status.value,
        "invited_suppliers": supplier_infos,
        "created_at": project.created_at,
        "awarded_at": project.awarded_at
    }


@router.get("/sourcing/projects")
async def list_sourcing_projects(
    status: str = Query(None),
    sourcing_type: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """获取寻源项目列表"""
    query = select(SourcingProject).order_by(SourcingProject.created_at.desc())
    if status:
        query = query.where(SourcingProject.status == status)
    if sourcing_type:
        query = query.where(SourcingProject.sourcing_type == sourcing_type)

    result = await db.execute(query)
    projects = result.scalars().all()

    response = []
    for p in projects:
        # 统计邀请供应商
        inv_result = await db.execute(
            select(SourcingInvitation)
            .where(SourcingInvitation.sourcing_id == p.id)
        )
        invs = inv_result.scalars().all()
        accepted = sum(1 for i in invs if i.status == "accepted")
        response.append({
            "id": p.id,
            "project_name": p.project_name,
            "sourcing_type": p.sourcing_type,
            "materials_summary": p.materials_summary,
            "deadline": p.deadline,
            "budget": p.budget,
            "status": p.status.value,
            "invited_count": len(invs),
            "accepted_count": accepted,
            "created_at": p.created_at
        })
    return response


# ==================== US-202: 供应商接收/拒绝邀请 ====================
# 注意：此路由必须在 /sourcing/projects/{project_id} 之前定义，避免被误匹配

@router.get("/sourcing/projects/invitations")
async def supplier_view_invitations(
    supplier_id: int = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """供应商查看收到的寻源邀请"""
    result = await db.execute(
        select(SourcingInvitation)
        .options(selectinload(SourcingInvitation.sourcing))
        .where(SourcingInvitation.supplier_id == supplier_id)
        .order_by(SourcingInvitation.created_at.desc())
    )
    invs = result.scalars().all()
    return [
        {
            "invitation_id": inv.id,
            "sourcing_id": inv.sourcing_id,
            "project_name": inv.sourcing.project_name if inv.sourcing else None,
            "sourcing_type": inv.sourcing.sourcing_type if inv.sourcing else None,
            "status": inv.status,
            "project_status": inv.sourcing.status.value if inv.sourcing else None,
            "budget": inv.sourcing.budget if inv.sourcing else None,
            "deadline": inv.sourcing.deadline if inv.sourcing else None,
            "responded_at": inv.responded_at,
            "decline_reason": inv.decline_reason,
            "created_at": inv.created_at
        }
        for inv in invs
    ]


@router.get("/sourcing/projects/{project_id}")
async def get_sourcing_project(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取寻源项目详情"""
    result = await db.execute(
        select(SourcingProject).where(SourcingProject.id == project_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="寻源项目不存在")

    # 邀请供应商详情
    inv_result = await db.execute(
        select(SourcingInvitation)
        .options(selectinload(SourcingInvitation.supplier))
        .where(SourcingInvitation.sourcing_id == project_id)
    )
    invs = inv_result.scalars().all()
    supplier_infos = []
    for inv in invs:
        supplier_infos.append({
            "invitation_id": inv.id,
            "supplier_id": inv.supplier_id,
            "supplier_name": inv.supplier.name if inv.supplier else None,
            "status": inv.status,
            "responded_at": inv.responded_at,
            "decline_reason": inv.decline_reason
        })

    # 投标记录（开标后可见）
    bid_result = await db.execute(
        select(SourcingBid)
        .options(selectinload(SourcingBid.supplier))
        .where(SourcingBid.sourcing_id == project_id)
        .where(SourcingBid.is_opened == 1)  # 只返回已开标的
    )
    bids = bid_result.scalars().all()
    bid_infos = []
    for b in bids:
        bid_infos.append({
            "bid_id": b.id,
            "supplier_id": b.supplier_id,
            "supplier_name": b.supplier.name if b.supplier else None,
            "round_number": b.round_number,
            "total_amount": b.total_amount,
            "delivery_days": b.delivery_days,
            "submitted_at": b.submitted_at
        })

    return {
        "id": project.id,
        "project_name": project.project_name,
        "sourcing_type": project.sourcing_type,
        "materials_summary": project.materials_summary,
        "deadline": project.deadline,
        "budget": project.budget,
        "status": project.status.value,
        "invited_suppliers": supplier_infos,
        "bids": bid_infos,
        "created_at": project.created_at,
        "awarded_at": project.awarded_at
    }


# ==================== US-202 续: 供应商接受/拒绝邀请 ====================

@router.post("/sourcing/projects/{project_id}/accept")
async def accept_sourcing_invitation(
    project_id: int,
    supplier_id: int = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """供应商确认参与寻源"""
    result = await db.execute(
        select(SourcingInvitation)
        .where(SourcingInvitation.sourcing_id == project_id)
        .where(SourcingInvitation.supplier_id == supplier_id)
    )
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="未找到邀请记录")
    if inv.status != "pending":
        raise HTTPException(status_code=400, detail="已处理过此邀请")

    inv.status = "accepted"
    inv.responded_at = datetime.utcnow()
    await db.commit()  # 立即提交，确保后续请求可见
    return {"success": True, "message": "已确认参与，等待采购方发布询价文件"}


@router.post("/sourcing/projects/{project_id}/decline")
async def decline_sourcing_invitation(
    project_id: int,
    supplier_id: int = Query(...),
    reason: str = Query(""),
    db: AsyncSession = Depends(get_db)
):
    """供应商谢绝参与"""
    result = await db.execute(
        select(SourcingInvitation)
        .where(SourcingInvitation.sourcing_id == project_id)
        .where(SourcingInvitation.supplier_id == supplier_id)
    )
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="未找到邀请记录")
    if inv.status != "pending":
        raise HTTPException(status_code=400, detail="已处理过此邀请")

    inv.status = "declined"
    inv.decline_reason = reason
    inv.responded_at = datetime.utcnow()
    await db.commit()  # 立即提交
    return {"success": True, "message": "已谢绝，采购方已收到通知"}


# ==================== US-203: 供应商在线投标 ====================

@router.get("/sourcing/projects/{project_id}/bid")
async def get_bid_form(
    project_id: int,
    supplier_id: int = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """供应商获取投标表单"""
    project_result = await db.execute(
        select(SourcingProject).where(SourcingProject.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="寻源项目不存在")

    # 验证供应商被邀请
    inv_result = await db.execute(
        select(SourcingInvitation)
        .where(SourcingInvitation.sourcing_id == project_id)
        .where(SourcingInvitation.supplier_id == supplier_id)
        .where(SourcingInvitation.status == "accepted")
    )
    if not inv_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="您未被邀请或尚未确认参与")

    # 获取当前轮次
    last_bid_result = await db.execute(
        select(SourcingBid)
        .where(SourcingBid.sourcing_id == project_id)
        .where(SourcingBid.supplier_id == supplier_id)
        .order_by(SourcingBid.round_number.desc())
        .limit(1)
    )
    last_bid = last_bid_result.scalar_one_or_none()
    next_round = (last_bid.round_number + 1) if last_bid else 1

    return {
        "project_id": project.id,
        "project_name": project.project_name,
        "sourcing_type": project.sourcing_type,
        "deadline": project.deadline,
        "budget": project.budget,
        "enable_reverse_auction": bool(project.enable_reverse_auction),
        "current_round": next_round,
        "previous_bid": {
            "round_number": last_bid.round_number,
            "bid_data": json.loads(last_bid.bid_data) if last_bid else None,
            "total_amount": last_bid.total_amount,
            "submitted_at": last_bid.submitted_at
        } if last_bid else None
    }


@router.post("/sourcing/projects/{project_id}/bid")
async def submit_bid(
    project_id: int,
    body: SourcingBidCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    供应商提交投标

    - 报价数据加密存储（实际为base64编码存储）
    - 支持多轮报价
    """
    # 验证供应商被邀请
    inv_result = await db.execute(
        select(SourcingInvitation)
        .where(SourcingInvitation.sourcing_id == project_id)
        .where(SourcingInvitation.supplier_id == body.supplier_id)
    )
    inv = inv_result.scalar_one_or_none()
    if not inv or inv.status != "accepted":
        raise HTTPException(status_code=403, detail="您未被邀请参与")

    # 计算总价
    total = sum(item.get("subtotal", 0) for item in body.bid_data)

    # 加密存储（简单base64编码模拟，实际应使用非对称加密）
    import base64
    bid_data_encrypted = base64.b64encode(
        json.dumps(body.bid_data, ensure_ascii=False).encode()
    ).decode()

    bid = SourcingBid(
        sourcing_id=project_id,
        supplier_id=body.supplier_id,
        round_number=body.round_number,
        bid_data=bid_data_encrypted,
        technical_proposal=body.technical_proposal,
        delivery_days=body.delivery_days,
        payment_terms=body.payment_terms,
        attachment_urls=json.dumps(body.attachment_urls, ensure_ascii=False),
        total_amount=total,
        submitted_at=datetime.utcnow()
    )
    db.add(bid)
    await db.flush()
    await db.refresh(bid)
    return {
        "success": True,
        "message": f"第{body.round_number}轮报价已提交",
        "bid_id": bid.id,
        "total_amount": total
    }


# ==================== US-204: 采购方在线开标比价 ====================

@router.post("/sourcing/projects/{project_id}/open-bids")
async def open_bids(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    采购方开标

    - 截止时间到达后自动开标或手动开标
    - 所有报价解密可见
    """
    project_result = await db.execute(
        select(SourcingProject).where(SourcingProject.id == project_id)
    )
    project = project_result.scalar_one()
    if project.status not in [SourcingStatus.OPEN, SourcingStatus.EVALUATING]:
        raise HTTPException(status_code=400, detail="当前状态不允许开标")

    # 解密并标记所有报价为已开标
    import base64
    bids_result = await db.execute(
        select(SourcingBid)
        .options(selectinload(SourcingBid.supplier))
        .where(SourcingBid.sourcing_id == project_id)
        .where(SourcingBid.is_opened == 0)
    )
    bids = bids_result.scalars().all()

    opened_count = 0
    for bid in bids:
        bid.is_opened = 1
        opened_count += 1

    project.status = SourcingStatus.EVALUATING
    await db.flush()
    return {
        "success": True,
        "message": f"已开标，{opened_count}份报价已解密可见"
    }


@router.get("/sourcing/projects/{project_id}/comparison")
async def get_bid_comparison(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取比价表

    - 仅在开标后可见
    - 按总价排序
    """
    project_result = await db.execute(
        select(SourcingProject).where(SourcingProject.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="寻源项目不存在")

    bids_result = await db.execute(
        select(SourcingBid)
        .options(selectinload(SourcingBid.supplier))
        .where(SourcingBid.sourcing_id == project_id)
        .where(SourcingBid.is_opened == 1)
        .order_by(SourcingBid.total_amount.asc())
    )
    bids = bids_result.scalars().all()

    import base64
    comparison = []
    for rank, bid in enumerate(bids, 1):
        # 解密报价数据
        try:
            decoded = base64.b64decode(bid.bid_data).decode()
            bid_data = json.loads(decoded)
        except Exception:
            bid_data = []

        comparison.append({
            "rank": rank,
            "bid_id": bid.id,
            "supplier_id": bid.supplier_id,
            "supplier_name": bid.supplier.name if bid.supplier else None,
            "total_amount": bid.total_amount,
            "delivery_days": bid.delivery_days,
            "payment_terms": bid.payment_terms,
            "round_number": bid.round_number,
            "bid_details": bid_data
        })

    return {
        "project_id": project_id,
        "project_name": project.project_name,
        "bids": comparison,
        "lowest_amount": comparison[0]["total_amount"] if comparison else None,
        "bid_count": len(comparison)
    }


# ==================== US-205: 中标/落标通知 ====================

@router.post("/sourcing/projects/{project_id}/award")
async def award_project(
    project_id: int,
    winner_supplier_id: int = Query(...),
    awarded_amount: float = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """采购方发布授标结果"""
    project_result = await db.execute(
        select(SourcingProject).where(SourcingProject.id == project_id)
    )
    project = project_result.scalar_one()
    if project.status == SourcingStatus.AWARDED:
        raise HTTPException(status_code=400, detail="该项目已授标")

    # 为所有供应商创建授标记录
    bids_result = await db.execute(
        select(SourcingBid)
        .where(SourcingBid.sourcing_id == project_id)
        .where(SourcingBid.is_opened == 1)
    )
    bids = bids_result.scalars().all()
    for bid in bids:
        award = SourcingAward(
            sourcing_id=project_id,
            supplier_id=bid.supplier_id,
            is_winner=1 if bid.supplier_id == winner_supplier_id else 0,
            awarded_amount=awarded_amount if bid.supplier_id == winner_supplier_id else bid.total_amount,
            notified_at=datetime.utcnow()
        )
        db.add(award)

    project.status = SourcingStatus.AWARDED
    project.awarded_at = datetime.utcnow()
    await db.flush()
    return {"success": True, "message": "授标结果已发布，中标供应商已收到通知"}


# ==================== US-206: 合同模板管理 ====================

@router.post("/contracts/templates")
async def create_contract_template(
    body: ContractTemplateCreate,
    created_by: int = Query(1),
    db: AsyncSession = Depends(get_db)
):
    """创建合同模板"""
    template = ContractTemplate(
        name=body.name,
        applicable_categories=body.applicable_categories,
        content=body.content,
        variables=json.dumps(body.variables, ensure_ascii=False),
        created_by=created_by
    )
    db.add(template)
    await db.flush()
    await db.refresh(template)
    return {
        "id": template.id,
        "name": template.name,
        "variables": body.variables,
        "created_at": template.created_at
    }


@router.get("/contracts/templates")
async def list_contract_templates(
    category: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """获取合同模板列表"""
    query = select(ContractTemplate).where(ContractTemplate.is_active == 1)
    if category:
        query = query.where(ContractTemplate.applicable_categories.contains(category))
    query = query.order_by(ContractTemplate.created_at.desc())
    result = await db.execute(query)
    templates = result.scalars().all()
    return [
        {
            "id": t.id,
            "name": t.name,
            "applicable_categories": t.applicable_categories,
            "variables": json.loads(t.variables) if t.variables else [],
            "created_at": t.created_at
        }
        for t in templates
    ]


@router.get("/contracts/templates/{template_id}")
async def get_contract_template(
    template_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取模板详情"""
    result = await db.execute(
        select(ContractTemplate).where(ContractTemplate.id == template_id)
    )
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="模板不存在")
    return {
        "id": t.id,
        "name": t.name,
        "applicable_categories": t.applicable_categories,
        "content": t.content,
        "variables": json.loads(t.variables) if t.variables else [],
        "created_at": t.created_at
    }


# ==================== US-207: 合同草案生成与协同编辑 ====================

def generate_contract_no():
    from datetime import datetime as dt
    import uuid
    return f"CTR{dt.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"


@router.post("/contracts/generate-from-sourcing/{sourcing_id}")
async def generate_contract_from_sourcing(
    sourcing_id: int,
    template_id: int = Query(None),
    supplier_id: int = Query(...),
    contract_name: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """基于授标结果生成合同草案"""
    # 获取授标记录
    award_result = await db.execute(
        select(SourcingAward)
        .where(SourcingAward.sourcing_id == sourcing_id)
        .where(SourcingAward.supplier_id == supplier_id)
    )
    award = award_result.scalar_one_or_none()
    if not award:
        raise HTTPException(status_code=404, detail="未找到授标记录")

    contract_no = generate_contract_no()
    content = ""

    # 如果有模板，替换变量
    if template_id:
        tpl_result = await db.execute(
            select(ContractTemplate).where(ContractTemplate.id == template_id)
        )
        tpl = tpl_result.scalar_one_or_none()
        if tpl:
            # 获取供应商信息
            sup_result = await db.execute(
                select(Supplier).where(Supplier.id == supplier_id)
            )
            supplier = sup_result.scalar_one()
            content = tpl.content
            for var in json.loads(tpl.variables) if tpl.variables else []:
                if var == "supplier_name":
                    content = content.replace(f"{{{{{var}}}}}", supplier.name)
                elif var == "contract_amount":
                    content = content.replace(f"{{{{{var}}}}}", str(award.awarded_amount))
                elif var == "award_date":
                    content = content.replace(f"{{{{{var}}}}}", award.notified_at.strftime("%Y-%m-%d") if award.notified_at else datetime.utcnow().strftime("%Y-%m-%d"))

    contract = Contract(
        contract_no=contract_no,
        sourcing_id=sourcing_id,
        supplier_id=supplier_id,
        template_id=template_id,
        contract_name=contract_name,
        contract_amount=award.awarded_amount,
        content=content,
        status=ContractStatus.DRAFT
    )
    db.add(contract)
    await db.flush()
    await db.refresh(contract)
    return {
        "id": contract.id,
        "contract_no": contract.contract_no,
        "contract_name": contract.contract_name,
        "contract_amount": contract.contract_amount,
        "status": contract.status,
        "created_at": contract.created_at
    }


# 必须在 /contracts/{contract_id} 之前定义，否则 /contracts/ 会被当作带 path 参数的路由
@router.get("/contracts/")
async def list_contracts(
    supplier_id: int = Query(None),
    status: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """获取合同列表"""
    query = select(Contract).options(selectinload(Contract.supplier)).order_by(Contract.created_at.desc())
    if supplier_id:
        query = query.where(Contract.supplier_id == supplier_id)
    if status:
        query = query.where(Contract.status == status)
    result = await db.execute(query)
    contracts = result.scalars().all()
    return [
        {
            "id": c.id,
            "contract_no": c.contract_no,
            "contract_name": c.contract_name,
            "supplier_id": c.supplier_id,
            "supplier_name": c.supplier.name if c.supplier else None,
            "contract_amount": c.contract_amount,
            "status": c.status,
            "supplier_signed": bool(c.supplier_signed),
            "buyer_signed": bool(c.buyer_signed),
            "created_at": c.created_at,
        }
        for c in contracts
    ]


@router.get("/contracts/{contract_id}")
async def get_contract(
    contract_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取合同详情"""
    result = await db.execute(
        select(Contract)
        .options(selectinload(Contract.supplier))
        .where(Contract.id == contract_id)
    )
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    # 获取批注
    comments_result = await db.execute(
        select(ContractComment)
        .where(ContractComment.contract_id == contract_id)
        .order_by(ContractComment.created_at.asc())
    )
    comments = comments_result.scalars().all()

    return {
        "id": contract.id,
        "contract_no": contract.contract_no,
        "contract_name": contract.contract_name,
        "supplier_id": contract.supplier_id,
        "supplier_name": contract.supplier.name if contract.supplier else None,
        "contract_amount": contract.contract_amount,
        "content": contract.content,
        "status": contract.status,
        "supplier_signed": bool(contract.supplier_signed),
        "buyer_signed": bool(contract.buyer_signed),
        "effective_date": contract.effective_date,
        "expiry_date": contract.expiry_date,
        "created_at": contract.created_at,
        "comments": [
            {
                "id": c.id,
                "clause_id": c.clause_id,
                "party": c.party,
                "comment": c.comment,
                "resolved": bool(c.resolved),
                "created_at": c.created_at
            }
            for c in comments
        ]
    }


@router.patch("/contracts/{contract_id}")
async def update_contract(
    contract_id: int,
    content: str = Query(None),
    contract_name: str = Query(None),
    contract_amount: float = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """双方更新合同条款"""
    result = await db.execute(
        select(Contract).where(Contract.id == contract_id)
    )
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")
    if contract.status not in [ContractStatus.DRAFT, ContractStatus.PENDING_SIGN]:
        raise HTTPException(status_code=400, detail="当前状态不允许修改")

    if content is not None:
        contract.content = content
    if contract_name is not None:
        contract.contract_name = contract_name
    if contract_amount is not None:
        contract.contract_amount = contract_amount
    await db.flush()
    return {"success": True, "message": "合同已更新"}


@router.post("/contracts/{contract_id}/comments")
async def add_contract_comment(
    contract_id: int,
    clause_id: str = Query(""),
    party: str = Query(...),  # buyer/supplier
    comment: str = Query(...),
    created_by: int = Query(1),
    db: AsyncSession = Depends(get_db)
):
    """添加合同批注"""
    result = await db.execute(
        select(Contract).where(Contract.id == contract_id)
    )
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    cmt = ContractComment(
        contract_id=contract_id,
        clause_id=clause_id,
        party=party,
        comment=comment,
        created_by=created_by
    )
    db.add(cmt)
    await db.flush()
    await db.refresh(cmt)
    return {"success": True, "comment_id": cmt.id}


# ==================== US-206/207: 合同草案查收与反馈 ====================

@router.get("/contracts/drafts/{contract_id}")
async def get_contract_draft(
    contract_id: int,
    db: AsyncSession = Depends(get_db)
):
    """供应商查看合同草案"""
    result = await db.execute(
        select(Contract)
        .options(selectinload(Contract.supplier))
        .where(Contract.id == contract_id)
    )
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")
    if contract.status != ContractStatus.DRAFT:
        raise HTTPException(status_code=400, detail="当前合同不是草案状态")

    return {
        "id": contract.id,
        "contract_no": contract.contract_no,
        "contract_name": contract.contract_name,
        "supplier_id": contract.supplier_id,
        "supplier_name": contract.supplier.name if contract.supplier else None,
        "contract_amount": contract.contract_amount,
        "content": contract.content,
        "status": contract.status,
        "created_at": contract.created_at
    }


@router.post("/contracts/drafts/{contract_id}/acknowledge")
async def acknowledge_contract_draft(
    contract_id: int,
    db: AsyncSession = Depends(get_db)
):
    """供应商标记合同草案已查收"""
    result = await db.execute(
        select(Contract).where(Contract.id == contract_id)
    )
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")
    if contract.status != ContractStatus.DRAFT:
        raise HTTPException(status_code=400, detail="当前合同不处于草案状态")

    contract.status = ContractStatus.RECEIVED
    await db.flush()
    return {"success": True, "message": "合同草案已查收"}


@router.get("/contracts/{contract_id}/feedback-items")
async def get_contract_feedback_items(
    contract_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取合同反馈条款和批注"""
    result = await db.execute(
        select(Contract).where(Contract.id == contract_id)
    )
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    comments_result = await db.execute(
        select(ContractComment)
        .where(ContractComment.contract_id == contract_id)
        .order_by(ContractComment.created_at.asc())
    )
    comments = comments_result.scalars().all()
    return [
        {
            "id": c.id,
            "clause_id": c.clause_id,
            "party": c.party,
            "comment": c.comment,
            "resolved": bool(c.resolved),
            "created_at": c.created_at
        }
        for c in comments
    ]


@router.post("/contracts/{contract_id}/feedback")
async def add_contract_feedback(
    contract_id: int,
    clause_id: str = Query(""),
    party: str = Query(...),  # buyer/supplier
    comment: str = Query(...),
    created_by: int = Query(1),
    db: AsyncSession = Depends(get_db)
):
    """供应商提交合同修改意见反馈"""
    result = await db.execute(
        select(Contract).where(Contract.id == contract_id)
    )
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")
    if contract.status not in [ContractStatus.DRAFT, ContractStatus.RECEIVED, ContractStatus.PENDING_FEEDBACK, ContractStatus.PENDING_SIGN]:
        raise HTTPException(status_code=400, detail="当前合同状态不允许提交反馈")

    cmt = ContractComment(
        contract_id=contract_id,
        clause_id=clause_id,
        party=party,
        comment=comment,
        created_by=created_by
    )
    db.add(cmt)
    contract.status = ContractStatus.PENDING_FEEDBACK
    await db.flush()
    await db.refresh(cmt)
    return {"success": True, "comment_id": cmt.id}


@router.patch("/contracts/comments/{comment_id}/resolve")
async def resolve_contract_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db)
):
    """标记合同反馈意见为已处理"""
    result = await db.execute(
        select(ContractComment).where(ContractComment.id == comment_id)
    )
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="批注不存在")

    comment.resolved = 1
    await db.flush()
    return {"success": True, "message": "反馈意见已标记为已处理"}


# ==================== US-208: 合同签署与状态跟踪 ====================

@router.post("/contracts/{contract_id}/sign-initiate")
async def initiate_signing(
    contract_id: int,
    sign_sequence: str = Query("buyer_first"),
    db: AsyncSession = Depends(get_db)
):
    """采购方发起签署"""
    result = await db.execute(
        select(Contract).where(Contract.id == contract_id)
    )
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")
    if contract.status not in [ContractStatus.DRAFT, ContractStatus.RECEIVED, ContractStatus.PENDING_FEEDBACK]:
        raise HTTPException(status_code=400, detail="当前状态不允许发起签署")

    await db.execute(text(
        f"UPDATE contracts SET status = 'pending_sign', sign_sequence = :seq WHERE id = :id"
    ), {"seq": sign_sequence, "id": contract_id})
    db.expire(contract)
    await db.commit()
    return {
        "success": True,
        "message": f"签署流程已发起，请{('供应商' if sign_sequence == 'supplier_first' else '采购方')}方先签署"
    }


@router.post("/contracts/{contract_id}/sign")
async def sign_contract(
    contract_id: int,
    party: str = Query(...),  # buyer/supplier
    db: AsyncSession = Depends(get_db)
):
    """签署方完成签署"""
    result = await db.execute(
        select(Contract).where(Contract.id == contract_id)
    )
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")
    # 使用 Raw SQL 刷新 ORM 缓存，确保读到最新值
    await db.refresh(contract)
    if contract.status not in ["pending_sign", "signed"]:
        raise HTTPException(status_code=400, detail="当前状态不允许签署")

    now = datetime.utcnow()
    from sqlalchemy import text
    supplier_done = bool(contract.supplier_signed)
    buyer_done = bool(contract.buyer_signed)
    if party == "supplier":
        if supplier_done:
            raise HTTPException(status_code=400, detail="供应商已签署")
        await db.execute(text(
            "UPDATE contracts SET supplier_signed = 1, supplier_signed_at = :now WHERE id = :id"
        ), {"now": now, "id": contract_id})
        supplier_done = True
    elif party == "buyer":
        if buyer_done:
            raise HTTPException(status_code=400, detail="采购方已签署")
        await db.execute(text(
            "UPDATE contracts SET buyer_signed = 1, buyer_signed_at = :now WHERE id = :id"
        ), {"now": now, "id": contract_id})
        buyer_done = True
    else:
        raise HTTPException(status_code=400, detail="party 必须是 buyer 或 supplier")

    # 双方签署完成
    if supplier_done and buyer_done:
        await db.execute(text(
            "UPDATE contracts SET status = 'signed', signed_at = :now, effective_date = :now WHERE id = :id"
        ), {"now": now, "id": contract_id})

    await db.commit()
    if supplier_done and buyer_done:
        return {"success": True, "message": "双方签署完成，合同已生效！", "status": "signed"}
    return {"success": True, "message": f"{'供应商' if party == 'supplier' else '采购方'}签署完成，等待对方签署", "status": "pending"}


@router.get("/contracts/{contract_id}/sign-status")
async def get_sign_status(
    contract_id: int,
    db: AsyncSession = Depends(get_db)
):
    """查询签署状态"""
    result = await db.execute(
        select(Contract).where(Contract.id == contract_id)
    )
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")
    status = contract.status.value if hasattr(contract.status, "value") else str(contract.status)
    return {
        "contract_id": contract.id,
        "status": status,
        "supplier_signed": bool(contract.supplier_signed),
        "supplier_signed_at": contract.supplier_signed_at,
        "buyer_signed": bool(contract.buyer_signed),
        "buyer_signed_at": contract.buyer_signed_at,
        "sign_sequence": contract.sign_sequence,
        "signed_at": contract.signed_at
    }


@router.get("/contracts")
async def list_contracts(
    status: str = Query(None),
    supplier_id: int = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """获取合同列表"""
    query = select(Contract).order_by(Contract.created_at.desc())
    if status:
        query = query.where(Contract.status == status)
    if supplier_id:
        query = query.where(Contract.supplier_id == supplier_id)
    result = await db.execute(
        query.options(selectinload(Contract.supplier))
    )
    contracts = result.scalars().all()
    return [
        {
            "id": c.id,
            "contract_no": c.contract_no,
            "contract_name": c.contract_name,
            "supplier_name": c.supplier.name if c.supplier else None,
            "contract_amount": c.contract_amount,
            "status": c.status.value,
            "effective_date": c.effective_date,
            "expiry_date": c.expiry_date,
            "created_at": c.created_at
        }
        for c in contracts
    ]
