"""供应商准入与资格管理 API - Phase 1"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
import uuid
import json

from app.core.database import get_db
from app.models.supply_chain import (
    SupplierInvitation, SupplierRegistration, SupplierCertification,
    SupplierAlert, Supplier, InvitationStatus, RegistrationStatus,
    QualificationStatus
)
from app.schemas.supply_chain import (
    InvitationCreate, InvitationResponse, InvitationValidateResponse,
    RegistrationCreate, RegistrationResponse, AuditRequest,
    CertificationCreate, CertificationResponse, SupplierAlertResponse
)

router = APIRouter(prefix="/supplier-portal", tags=["供应商准入"])


def generate_invitation_code():
    """生成8位唯一邀请码"""
    return uuid.uuid4().hex[:8].upper()


# ==================== US-101: 供应商注册邀请 ====================

@router.post("/invitations", response_model=InvitationResponse)
async def create_invitation(
    body: InvitationCreate,
    created_by: int = Query(1, description="创建人ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    创建供应商注册邀请

    - 生成唯一邀请码（8位）
    - 邀请码有效期7天（可配置）
    - 同一邮箱不可重复邀请
    """
    # 检查邮箱是否已有待处理邀请
    existing = await db.execute(
        select(SupplierInvitation).where(
            SupplierInvitation.invited_email == body.invited_email,
            SupplierInvitation.status == InvitationStatus.PENDING
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该邮箱已有待处理的邀请，请等待或取消后再试")

    # 生成唯一邀请码
    code = generate_invitation_code()
    while True:
        check = await db.execute(
            select(SupplierInvitation).where(SupplierInvitation.invitation_code == code)
        )
        if not check.scalar_one_or_none():
            break
        code = generate_invitation_code()

    # 创建邀请记录
    invitation = SupplierInvitation(
        invitation_code=code,
        invited_supplier_name=body.invited_supplier_name,
        invited_email=body.invited_email,
        invited_contact_person=body.invited_contact_person,
        status=InvitationStatus.PENDING,
        expiry_date=datetime.utcnow() + timedelta(days=body.expiry_days),
        created_by=created_by,
        notes=body.notes
    )
    db.add(invitation)
    await db.flush()
    await db.commit()
    await db.refresh(invitation)
    return invitation


@router.post("/cert-alerts/check")
async def trigger_cert_expiry_check(db: AsyncSession = Depends(get_db)):
    """
    手动触发资质到期检查

    检查所有供应商资质，到期前30/15/7/1天自动生成预警
    已过期资质自动标记并创建预警
    """
    await check_and_create_cert_expiry_alerts(db)
    return {"success": True, "message": "资质到期检查完成"}


@router.get("/invitations/{code}/validate", response_model=InvitationValidateResponse)
async def validate_invitation_code(
    code: str,
    db: AsyncSession = Depends(get_db)
):
    """
    验证邀请码有效性

    - 检查邀请码是否存在
    - 检查是否已使用/过期
    - 返回邀请人和被邀请供应商预填信息
    """
    invitation = await db.execute(
        select(SupplierInvitation).where(SupplierInvitation.invitation_code == code.upper())
    )
    inv = invitation.scalar_one_or_none()

    if not inv:
        return InvitationValidateResponse(
            valid=False, invitation_code=code,
            invited_supplier_name="", invited_email="",
            expiry_date=datetime.utcnow(),
            message="邀请码不存在"
        )

    now = datetime.utcnow()

    # 检查是否已使用
    if inv.status == InvitationStatus.ACCEPTED:
        return InvitationValidateResponse(
            valid=False, invitation_code=code,
            invited_supplier_name=inv.invited_supplier_name,
            invited_email=inv.invited_email,
            expiry_date=inv.expiry_date,
            message="该邀请码已被使用"
        )

    # 检查是否过期
    if inv.status == InvitationStatus.EXPIRED or inv.expiry_date < now:
        # 自动标记为过期
        if inv.status != InvitationStatus.EXPIRED:
            inv.status = InvitationStatus.EXPIRED
            await db.flush()
        return InvitationValidateResponse(
            valid=False, invitation_code=code,
            invited_supplier_name=inv.invited_supplier_name,
            invited_email=inv.invited_email,
            expiry_date=inv.expiry_date,
            message="邀请码已过期"
        )

    # 检查是否已取消
    if inv.status == InvitationStatus.CANCELLED:
        return InvitationValidateResponse(
            valid=False, invitation_code=code,
            invited_supplier_name=inv.invited_supplier_name,
            invited_email=inv.invited_email,
            expiry_date=inv.expiry_date,
            message="该邀请已被取消"
        )

    return InvitationValidateResponse(
        valid=True,
        invitation_code=inv.invitation_code,
        invited_supplier_name=inv.invited_supplier_name,
        invited_email=inv.invited_email,
        expiry_date=inv.expiry_date,
        message="邀请码有效"
    )


@router.get("/invitations")
async def list_invitations(
    status: str = Query(None, description="筛选状态"),
    email: str = Query(None, description="供应商端：按受邀邮箱筛选"),
    db: AsyncSession = Depends(get_db)
):
    """采购方查看所有邀请；供应商端传 email 查看发给自己的注册邀请 (US-101-2)"""
    query = select(SupplierInvitation).order_by(SupplierInvitation.created_at.desc())
    if email:
        query = query.where(SupplierInvitation.invited_email == email.strip())
    if status:
        query = query.where(SupplierInvitation.status == status)
    result = await db.execute(query)
    invitations = result.scalars().all()
    return [
        {
            "id": i.id,
            "invitation_code": i.invitation_code,
            "invited_supplier_name": i.invited_supplier_name,
            "invited_email": i.invited_email,
            "invited_contact_person": i.invited_contact_person,
            "status": i.status.value,
            "expiry_date": i.expiry_date,
            "created_at": i.created_at,
            "notes": i.notes
        }
        for i in invitations
    ]


@router.delete("/invitations/{invitation_id}")
async def cancel_invitation(
    invitation_id: int,
    db: AsyncSession = Depends(get_db)
):
    """取消邀请"""
    result = await db.execute(
        select(SupplierInvitation).where(SupplierInvitation.id == invitation_id)
    )
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="邀请不存在")
    if inv.status != InvitationStatus.PENDING:
        raise HTTPException(status_code=400, detail="只能取消待处理的邀请")

    inv.status = InvitationStatus.CANCELLED
    await db.flush()
    return {"success": True, "message": "邀请已取消"}


# ==================== US-102: 供应商自助注册 ====================

@router.post("/register", response_model=RegistrationResponse)
async def supplier_register(
    body: RegistrationCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    供应商自助注册

    - 凭邀请码注册（或无邀请码公开注册）
    - 同一统一社会信用代码不可重复注册
    - 注册后状态为'待审核'
    """
    # 检查统一社会信用代码唯一性
    existing = await db.execute(
        select(SupplierRegistration).where(
            SupplierRegistration.unified_credit_code == body.unified_credit_code
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该统一社会信用代码已被注册")

    # 查找邀请记录（如果有邀请码）
    invitation_id = None
    if body.invitation_code:
        inv_result = await db.execute(
            select(SupplierInvitation).where(
                SupplierInvitation.invitation_code == body.invitation_code.upper()
            )
        )
        inv = inv_result.scalar_one_or_none()
        if not inv:
            raise HTTPException(status_code=400, detail="邀请码无效")
        if inv.status != InvitationStatus.PENDING:
            raise HTTPException(status_code=400, detail="邀请码已失效")
        if inv.expiry_date < datetime.utcnow():
            raise HTTPException(status_code=400, detail="邀请码已过期")
        invitation_id = inv.id

    # 创建注册记录
    registration = SupplierRegistration(
        invitation_id=invitation_id,
        company_name=body.company_name,
        unified_credit_code=body.unified_credit_code,
        contact_person=body.contact_person,
        contact_phone=body.contact_phone,
        contact_email=body.contact_email,
        address=body.address,
        main_categories=body.main_categories,
        annual_capacity=body.annual_capacity or 0.0,
        employee_count=body.employee_count or 0,
        established_year=body.established_year,
        status=RegistrationStatus.PENDING_AUDIT
    )
    db.add(registration)

    # 如果有邀请码，标记为已接受
    if invitation_id:
        inv.status = InvitationStatus.ACCEPTED
        inv.accepted_at = datetime.utcnow()

    await db.flush()
    await db.refresh(registration)
    return registration


@router.get("/register/status")
async def check_registration_status(
    unified_credit_code: str = Query(..., description="统一社会信用代码"),
    db: AsyncSession = Depends(get_db)
):
    """供应商查询自己的注册状态"""
    result = await db.execute(
        select(SupplierRegistration).where(
            SupplierRegistration.unified_credit_code == unified_credit_code
        )
    )
    reg = result.scalar_one_or_none()
    if not reg:
        return {"found": False, "message": "未找到注册记录"}

    return {
        "found": True,
        "id": reg.id,
        "company_name": reg.company_name,
        "status": reg.status.value,
        "audit_opinion": reg.audit_opinion,
        "created_at": reg.created_at
    }


# ==================== US-103: 采购方审核注册 ====================

@router.get("/pending-audit")
async def list_pending_audit(
    db: AsyncSession = Depends(get_db)
):
    """采购方获取待审核列表"""
    result = await db.execute(
        select(SupplierRegistration)
        .where(SupplierRegistration.status == RegistrationStatus.PENDING_AUDIT)
        .order_by(SupplierRegistration.created_at.asc())
    )
    registrations = result.scalars().all()
    return [
        {
            "id": r.id,
            "company_name": r.company_name,
            "unified_credit_code": r.unified_credit_code,
            "contact_person": r.contact_person,
            "contact_phone": r.contact_phone,
            "contact_email": r.contact_email,
            "address": r.address,
            "main_categories": r.main_categories,
            "annual_capacity": r.annual_capacity,
            "employee_count": r.employee_count,
            "established_year": r.established_year,
            "status": r.status.value,
            "created_at": r.created_at
        }
        for r in registrations
    ]


@router.get("/registrations/{registration_id}")
async def get_registration_detail(
    registration_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取注册详情"""
    result = await db.execute(
        select(SupplierRegistration).where(SupplierRegistration.id == registration_id)
    )
    reg = result.scalar_one_or_none()
    if not reg:
        raise HTTPException(status_code=404, detail="注册记录不存在")

    # 获取关联的邀请信息
    invitation_info = None
    if reg.invitation_id:
        inv_result = await db.execute(
            select(SupplierInvitation).where(SupplierInvitation.id == reg.invitation_id)
        )
        inv = inv_result.scalar_one_or_none()
        if inv:
            invitation_info = {
                "invitation_code": inv.invitation_code,
                "created_by": inv.created_by,
                "created_at": inv.created_at
            }

    return {
        "id": reg.id,
        "company_name": reg.company_name,
        "unified_credit_code": reg.unified_credit_code,
        "contact_person": reg.contact_person,
        "contact_phone": reg.contact_phone,
        "contact_email": reg.contact_email,
        "address": reg.address,
        "main_categories": reg.main_categories,
        "annual_capacity": reg.annual_capacity,
        "employee_count": reg.employee_count,
        "established_year": reg.established_year,
        "status": reg.status.value,
        "audit_opinion": reg.audit_opinion,
        "audited_by": reg.audited_by,
        "audited_at": reg.audited_at,
        "created_at": reg.created_at,
        "invitation": invitation_info
    }


@router.post("/registrations/{registration_id}/audit")
async def audit_registration(
    registration_id: int,
    body: AuditRequest,
    auditor_id: int = Query(1, description="审核人ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    采购方审核注册申请

    - 审核通过: 创建正式的 supplier 记录，状态变为'已通过'
    - 审核驳回: 记录驳回原因，供应商可修改后重新提交
    """
    result = await db.execute(
        select(SupplierRegistration).where(SupplierRegistration.id == registration_id)
    )
    reg = result.scalar_one_or_none()
    if not reg:
        raise HTTPException(status_code=404, detail="注册记录不存在")
    if reg.status not in [RegistrationStatus.PENDING_AUDIT, RegistrationStatus.AUDITING]:
        raise HTTPException(status_code=400, detail="该注册申请已处理")

    if body.action == "approve":
        # 审核通过: 创建供应商主数据
        from app.models.supply_chain import SupplierStatus
        supplier = Supplier(
            name=reg.company_name,
            contact_person=reg.contact_person,
            phone=reg.contact_phone,
            email=reg.contact_email,
            address=reg.address,
            status=SupplierStatus.ACTIVE,
            origin_type="一般产区",
            main_category=reg.main_categories,
            annual_capacity=reg.annual_capacity or 0.0
        )
        db.add(supplier)
        await db.flush()
        await db.refresh(supplier)

        # 更新注册记录
        reg.status = RegistrationStatus.APPROVED
        reg.supplier_id = supplier.id
        reg.audit_opinion = body.opinion
        reg.audited_by = auditor_id
        reg.audited_at = datetime.utcnow()

        await db.flush()
        return {
            "success": True,
            "message": "审核通过，供应商已创建",
            "supplier_id": supplier.id,
            "supplier_name": supplier.name
        }

    elif body.action == "reject":
        reg.status = RegistrationStatus.REJECTED
        reg.audit_opinion = body.opinion
        reg.audited_by = auditor_id
        reg.audited_at = datetime.utcnow()
        await db.flush()
        return {
            "success": True,
            "message": "审核驳回，已通知供应商"
        }
    else:
        raise HTTPException(status_code=400, detail="action 必须是 approve 或 reject")


@router.post("/registrations/{registration_id}/resubmit")
async def resubmit_registration(
    registration_id: int,
    body: RegistrationCreate,
    db: AsyncSession = Depends(get_db)
):
    """被驳回的注册申请重新提交"""
    result = await db.execute(
        select(SupplierRegistration).where(SupplierRegistration.id == registration_id)
    )
    reg = result.scalar_one_or_none()
    if not reg:
        raise HTTPException(status_code=404, detail="注册记录不存在")
    if reg.status != RegistrationStatus.REJECTED:
        raise HTTPException(status_code=400, detail="只有被驳回的申请可以重新提交")

    # 更新注册信息
    reg.company_name = body.company_name
    reg.unified_credit_code = body.unified_credit_code
    reg.contact_person = body.contact_person
    reg.contact_phone = body.contact_phone
    reg.contact_email = body.contact_email
    reg.address = body.address
    reg.main_categories = body.main_categories
    reg.annual_capacity = body.annual_capacity or 0.0
    reg.employee_count = body.employee_count or 0
    reg.established_year = body.established_year
    reg.status = RegistrationStatus.PENDING_AUDIT
    reg.audit_opinion = None
    reg.audited_by = None
    reg.audited_at = None
    await db.flush()
    return {"success": True, "message": "重新提交成功，等待审核"}


# ==================== US-108: 资质证书与过期预警 ====================

@router.post("/suppliers/{supplier_id}/certifications", response_model=CertificationResponse)
async def add_supplier_certification(
    supplier_id: int,
    body: CertificationCreate,
    db: AsyncSession = Depends(get_db)
):
    """添加供应商资质证书"""
    # 检查供应商是否存在
    supplier = await db.execute(
        select(Supplier).where(Supplier.id == supplier_id)
    )
    if not supplier.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="供应商不存在")

    cert = SupplierCertification(
        supplier_id=supplier_id,
        cert_type=body.cert_type,
        cert_name=body.cert_name,
        cert_no=body.cert_no,
        issue_date=body.issue_date,
        expiry_date=body.expiry_date,
        cert_file_url=body.cert_file_url,
        status="valid"
    )
    db.add(cert)
    await db.flush()
    await db.refresh(cert)
    now = datetime.utcnow()
    cert.days_until_expiry = max(0, (cert.expiry_date - now).days)
    return {
        "id": cert.id,
        "supplier_id": cert.supplier_id,
        "cert_type": cert.cert_type,
        "cert_name": cert.cert_name,
        "cert_no": cert.cert_no,
        "issue_date": cert.issue_date,
        "expiry_date": cert.expiry_date,
        "cert_file_url": cert.cert_file_url,
        "status": cert.status,
        "days_until_expiry": cert.days_until_expiry,
        "created_at": cert.created_at
    }


@router.get("/suppliers/{supplier_id}/certifications")
async def list_supplier_certifications(
    supplier_id: int,
    db: AsyncSession = Depends(get_db)
):
    """查看供应商所有资质证书及有效期"""
    result = await db.execute(
        select(SupplierCertification)
        .where(SupplierCertification.supplier_id == supplier_id)
        .order_by(SupplierCertification.expiry_date.asc())
    )
    certs = result.scalars().all()
    now = datetime.utcnow()
    return [
        {
            "id": c.id,
            "supplier_id": c.supplier_id,
            "cert_type": c.cert_type,
            "cert_name": c.cert_name,
            "cert_no": c.cert_no,
            "issue_date": c.issue_date,
            "expiry_date": c.expiry_date,
            "cert_file_url": c.cert_file_url,
            "status": c.status,
            "days_until_expiry": max(0, (c.expiry_date - now).days),
            "created_at": c.created_at
        }
        for c in certs
    ]


@router.get("/supplier-alerts")
async def list_supplier_alerts(
    is_resolved: int = Query(None, description="0=未处理, 1=已处理"),
    db: AsyncSession = Depends(get_db)
):
    """采购方查看所有供应商资质预警列表"""
    query = (
        select(SupplierAlert)
        .options(selectinload(SupplierAlert.supplier))
        .join(Supplier)
        .order_by(SupplierAlert.created_at.desc())
    )
    if is_resolved is not None:
        query = query.where(SupplierAlert.is_resolved == is_resolved)
    result = await db.execute(query)
    alerts = result.scalars().all()
    return [
        {
            "id": a.id,
            "supplier_id": a.supplier_id,
            "alert_type": a.alert_type,
            "message": a.message,
            "days_before_expiry": a.days_before_expiry,
            "is_read": a.is_read,
            "is_resolved": a.is_resolved,
            "created_at": a.created_at,
            "supplier_name": a.supplier.name if a.supplier else None
        }
        for a in alerts
    ]


@router.post("/supplier-alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db)
):
    """标记预警为已处理"""
    result = await db.execute(
        select(SupplierAlert).where(SupplierAlert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="预警不存在")

    alert.is_resolved = 1
    alert.is_read = 1
    alert.resolved_at = datetime.utcnow()
    await db.flush()
    return {"success": True, "message": "预警已处理"}


async def check_and_create_cert_expiry_alerts(db: AsyncSession):
    """后台任务: 检查资质到期并创建预警"""
    now = datetime.utcnow()
    warning_days = [30, 15, 7, 1]

    for days in warning_days:
        target_date = now + timedelta(days=days)

        # 查找即将到期的资质（尚未创建预警）
        result = await db.execute(
            select(SupplierCertification)
            .where(SupplierCertification.expiry_date <= target_date)
            .where(SupplierCertification.expiry_date >= now)
            .where(SupplierCertification.status == "valid")
        )
        certs = result.scalars().all()

        for cert in certs:
            # 检查是否已有预警
            existing = await db.execute(
                select(SupplierAlert).where(
                    SupplierAlert.certification_id == cert.id,
                    SupplierAlert.days_before_expiry == days
                )
            )
            if not existing.scalar_one_or_none():
                alert = SupplierAlert(
                    supplier_id=cert.supplier_id,
                    alert_type="cert_expiring",
                    certification_id=cert.id,
                    message=f"【{cert.cert_name}】将于 {days} 天后（{cert.expiry_date.strftime('%Y-%m-%d')}）到期，请及时重认证",
                    days_before_expiry=days
                )
                db.add(alert)

        # 查找已过期的资质
        expired = await db.execute(
            select(SupplierCertification)
            .where(SupplierCertification.expiry_date < now)
            .where(SupplierCertification.status == "valid")
        )
        for cert in expired.scalars().all():
            cert.status = "expired"
            # 检查是否已有过期预警
            existing = await db.execute(
                select(SupplierAlert).where(
                    SupplierAlert.certification_id == cert.id,
                    SupplierAlert.alert_type == "cert_expired"
                )
            )
            if not existing.scalar_one_or_none():
                alert = SupplierAlert(
                    supplier_id=cert.supplier_id,
                    alert_type="cert_expired",
                    certification_id=cert.id,
                    message=f"【{cert.cert_name}】已于 {cert.expiry_date.strftime('%Y-%m-%d')} 到期，请立即重认证",
                    days_before_expiry=0
                )
                db.add(alert)

    await db.flush()
