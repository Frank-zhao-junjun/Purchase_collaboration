"""采购供应链协同数据模型"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PRODUCTION = "in_production"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class ProductStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    OUT_OF_STOCK = "out_of_stock"

class SupplierStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLACKLISTED = "blacklisted"

class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    contact_person = Column(String(100))
    phone = Column(String(50))
    email = Column(String(100))
    address = Column(String(500))
    status = Column(SQLEnum(SupplierStatus), default=SupplierStatus.ACTIVE)
    rating = Column(Float, default=5.0)
    # 供应商扩展字段（Phase 1 协同）
    origin_type = Column(String(50), default="一般产区")  # 核心产区/一般产区
    main_category = Column(String(100))  # 主营品类: 粮食类/酵母类/辅料类
    annual_capacity = Column(Float, default=0.0)  # 年供货能力(吨)
    cooperation_years = Column(Integer, default=0)  # 合作年限
    quality_score = Column(Float, default=5.0)  # 历史质量评分
    delivery_score = Column(Float, default=5.0)  # 交期评分
    service_score = Column(Float, default=5.0)  # 服务评分
    qualifications = Column(Text, default="[]")  # 资质证书 JSON 数组
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    materials = relationship("Material", back_populates="supplier")
    orders = relationship("PurchaseOrder", back_populates="supplier")

class Material(Base):
    __tablename__ = "materials"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    category = Column(String(100))
    unit = Column(String(50), default="吨")
    unit_price = Column(Float, default=0.0)
    stock_quantity = Column(Float, default=0.0)
    reorder_point = Column(Float, default=10.0)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    origin = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    supplier = relationship("Supplier", back_populates="materials")
    order_items = relationship("PurchaseOrderItem", back_populates="material")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    brand = Column(String(100))
    category = Column(String(100))
    abv = Column(Float, default=53.0)
    specification = Column(String(100))
    unit_price = Column(Float, default=0.0)
    stock_quantity = Column(Integer, default=0)
    status = Column(SQLEnum(ProductStatus), default=ProductStatus.ACTIVE)
    description = Column(String(1000))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    production_records = relationship("ProductionRecord", back_populates="product")
    sales_orders = relationship("SalesOrder", back_populates="product")

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(50), unique=True, nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    total_amount = Column(Float, default=0.0)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING)
    expected_delivery_date = Column(DateTime)
    actual_delivery_date = Column(DateTime)
    notes = Column(String(500))
    # 供应商协同字段（Phase 1）
    supplier_confirmed_at = Column(DateTime)  # 供应商确认时间
    supplier_rejection_reason = Column(String(500))  # 供应商拒绝原因
    created_by = Column(String(50), default="系统")  # 创建人
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    supplier = relationship("Supplier", back_populates="orders")
    items = relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan")

class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"
    id = Column(Integer, primary_key=True, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    purchase_order = relationship("PurchaseOrder", back_populates="items")
    material = relationship("Material", back_populates="order_items")

class ProductionRecord(Base):
    __tablename__ = "production_records"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    batch_no = Column(String(50), unique=True, nullable=False)
    production_date = Column(DateTime, default=datetime.utcnow)
    quantity = Column(Integer, nullable=False)
    qualified_quantity = Column(Integer, default=0)
    quality_rate = Column(Float, default=0.0)
    operator = Column(String(100))
    notes = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    product = relationship("Product", back_populates="production_records")
    material_usages = relationship("MaterialUsage", back_populates="production_record", cascade="all, delete-orphan")

class MaterialUsage(Base):
    __tablename__ = "material_usages"
    id = Column(Integer, primary_key=True, index=True)
    production_record_id = Column(Integer, ForeignKey("production_records.id"), nullable=False)
    material_name = Column(String(200), nullable=False)
    quantity = Column(Float, nullable=False)
    production_record = relationship("ProductionRecord", back_populates="material_usages")

class SalesOrder(Base):
    __tablename__ = "sales_orders"
    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(50), unique=True, nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    customer_name = Column(String(200), nullable=False)
    customer_contact = Column(String(100))
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING)
    shipping_address = Column(String(500))
    expected_ship_date = Column(DateTime)
    actual_ship_date = Column(DateTime)
    notes = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    product = relationship("Product", back_populates="sales_orders")

class Warehouse(Base):
    __tablename__ = "warehouses"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    location = Column(String(500))
    capacity = Column(Integer, default=0)
    current_stock = Column(Integer, default=0)
    manager = Column(String(100))
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)


# ==================== Phase 1: 协同模型 ====================

class ShipmentStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_TRANSIT = "in_transit"
    ARRIVED = "arrived"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class ShipmentNote(Base):
    """送货单(ASN) - 供应商创建的发货通知"""
    __tablename__ = "shipment_notes"
    id = Column(Integer, primary_key=True, index=True)
    shipment_no = Column(String(50), unique=True, nullable=False, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    status = Column(SQLEnum(ShipmentStatus), default=ShipmentStatus.DRAFT)
    carrier_name = Column(String(100))
    tracking_no = Column(String(100))
    vehicle_no = Column(String(50))
    driver_name = Column(String(50))
    driver_phone = Column(String(50))
    expected_arrival = Column(DateTime)
    actual_arrival = Column(DateTime)
    shipping_address = Column(String(500))
    receiving_warehouse = Column(String(200))
    notes = Column(String(500))
    total_quantity = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    purchase_order = relationship("PurchaseOrder")
    supplier = relationship("Supplier")
    items = relationship("ShipmentNoteItem", back_populates="shipment_note", cascade="all, delete-orphan")


class ShipmentNoteItem(Base):
    """送货单明细 - 含批次追溯信息"""
    __tablename__ = "shipment_note_items"
    id = Column(Integer, primary_key=True, index=True)
    shipment_note_id = Column(Integer, ForeignKey("shipment_notes.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    material_name = Column(String(200))
    quantity = Column(Float, nullable=False)
    unit = Column(String(50), default="吨")
    batch_no = Column(String(50))
    production_date = Column(DateTime)
    origin_location = Column(String(200))
    quality_grade = Column(String(50))
    package_count = Column(Integer, default=1)
    notes = Column(String(300))
    created_at = Column(DateTime, default=datetime.utcnow)
    shipment_note = relationship("ShipmentNote", back_populates="items")
    material = relationship("Material")


# ==================== Phase 1: 供应商协同模型 ====================

class InvitationStatus(str, enum.Enum):
    PENDING = "pending"       # 待接受
    ACCEPTED = "accepted"     # 已接受（供应商已注册）
    EXPIRED = "expired"       # 已过期
    CANCELLED = "cancelled"   # 已取消


class SupplierInvitation(Base):
    """供应商注册邀请"""
    __tablename__ = "supplier_invitations"

    id = Column(Integer, primary_key=True, index=True)
    invitation_code = Column(String(12), unique=True, nullable=False, index=True)
    invited_supplier_name = Column(String(200), nullable=False)
    invited_email = Column(String(100), nullable=False)
    invited_contact_person = Column(String(100))
    status = Column(SQLEnum(InvitationStatus), default=InvitationStatus.PENDING)
    expiry_date = Column(DateTime, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    accepted_at = Column(DateTime, nullable=True)
    notes = Column(String(500))


class RegistrationStatus(str, enum.Enum):
    PENDING_AUDIT = "pending_audit"    # 待审核
    AUDITING = "auditing"              # 审核中
    APPROVED = "approved"               # 已通过
    REJECTED = "rejected"              # 被驳回


class SupplierRegistration(Base):
    """供应商注册信息（独立于主数据表，审核通过后写入 suppliers）"""
    __tablename__ = "supplier_registrations"

    id = Column(Integer, primary_key=True, index=True)
    invitation_id = Column(Integer, ForeignKey("supplier_invitations.id"), nullable=True)
    # 企业基本信息
    company_name = Column(String(200), nullable=False, index=True)
    unified_credit_code = Column(String(18), nullable=False, unique=True, index=True)
    contact_person = Column(String(100), nullable=False)
    contact_phone = Column(String(50), nullable=False)
    contact_email = Column(String(100))
    address = Column(String(500))
    # 扩展信息
    business_license_url = Column(String(500))
    main_categories = Column(String(500))    # 主营产品类目，多个用逗号分隔
    annual_capacity = Column(Float, default=0.0)  # 年供货能力(吨)
    employee_count = Column(Integer, default=0)   # 员工规模
    established_year = Column(Integer)           # 成立年份
    # 注册状态
    status = Column(SQLEnum(RegistrationStatus), default=RegistrationStatus.PENDING_AUDIT)
    audit_opinion = Column(Text)                # 审核意见
    audited_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    audited_at = Column(DateTime, nullable=True)
    # 关联主数据（审核通过后）
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class QualificationStatus(str, enum.Enum):
    PENDING_RESPONSE = "pending_response"   # 待供应商响应
    IN_PROGRESS = "in_progress"             # 评审中
    SUPPLEMENT_MATERIALS = "supplement_materials"  # 补充材料
    APPROVED = "approved"                  # 已通过
    REJECTED = "rejected"                 # 未通过


class QualificationProject(Base):
    """供应商资格评审项目"""
    __tablename__ = "qualification_projects"

    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String(200), nullable=False)
    target_categories = Column(String(500))  # 评审品类，多个用逗号分隔
    deadline = Column(DateTime, nullable=True)
    status = Column(SQLEnum(QualificationStatus), default=QualificationStatus.PENDING_RESPONSE)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    notes = Column(Text)


class QualificationSubmission(Base):
    """供应商资格评审提交"""
    __tablename__ = "qualification_submissions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("qualification_projects.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    status = Column(SQLEnum(QualificationStatus), default=QualificationStatus.IN_PROGRESS)
    # 问卷答案 (JSON)
    questionnaire_answers = Column(Text, default="{}")
    # 评审评分
    tech_score = Column(Float, nullable=True)    # 技术能力得分
    quality_score = Column(Float, nullable=True)  # 质量体系得分
    finance_score = Column(Float, nullable=True)  # 财务状况得分
    final_score = Column(Float, nullable=True)   # 综合得分
    review_opinions = Column(Text)               # 评审意见
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    # 澄清记录
    clarification_requests = Column(Text, default="[]")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("QualificationProject")
    supplier = relationship("Supplier")


class SupplierCertification(Base):
    """供应商资质证书"""
    __tablename__ = "supplier_certifications"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    cert_type = Column(String(50), nullable=False)    # 资质类型: 营业执照/生产许可证/质量体系认证/行业资质
    cert_name = Column(String(200), nullable=False)    # 证书名称
    cert_no = Column(String(100))                       # 证书编号
    issue_date = Column(DateTime)                       # 发证日期
    expiry_date = Column(DateTime, nullable=False)     # 有效期
    cert_file_url = Column(String(500))                # 证书扫描件URL
    status = Column(String(20), default="valid")      # valid/expired/expiring
    created_at = Column(DateTime, default=datetime.utcnow)

    supplier = relationship("Supplier")


class SupplierAlert(Base):
    """供应商资质预警"""
    __tablename__ = "supplier_alerts"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    alert_type = Column(String(50), nullable=False)  # cert_expiring/cert_expired/qualification_expiring
    certification_id = Column(Integer, ForeignKey("supplier_certifications.id"), nullable=True)
    message = Column(String(500), nullable=False)
    days_before_expiry = Column(Integer, nullable=True)  # 到期前天数
    is_read = Column(Integer, default=0)              # 0=未读, 1=已读
    is_resolved = Column(Integer, default=0)         # 0=未处理, 1=已处理
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    supplier = relationship("Supplier")


# ==================== Phase 2: 寻源与合同模型 ====================

class SourcingStatus(str, enum.Enum):
    DRAFT = "draft"
    OPEN = "open"              # 寻源中
    EVALUATING = "evaluating"  # 评审中
    AWARDED = "awarded"        # 已授标
    CANCELLED = "cancelled"


class SourcingProject(Base):
    """寻源项目 (RFQ/RFP/RFI)"""
    __tablename__ = "sourcing_projects"

    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String(200), nullable=False)
    sourcing_type = Column(String(20), nullable=False)  # RFQ/RFP/RFI
    materials_summary = Column(Text)       # 物料概要
    deadline = Column(DateTime, nullable=True)
    budget = Column(Float, nullable=True)
    evaluation_criteria = Column(Text)     # 评审标准 JSON
    status = Column(SQLEnum(SourcingStatus), default=SourcingStatus.DRAFT)
    enable_reverse_auction = Column(Integer, default=0)  # 是否启用反向竞价
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    awarded_at = Column(DateTime, nullable=True)


class SourcingInvitation(Base):
    """寻源邀请"""
    __tablename__ = "sourcing_invitations"

    id = Column(Integer, primary_key=True, index=True)
    sourcing_id = Column(Integer, ForeignKey("sourcing_projects.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    status = Column(String(20), default="pending")  # pending/accepted/declined
    decline_reason = Column(String(300))
    responded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    sourcing = relationship("SourcingProject")
    supplier = relationship("Supplier")


class SourcingBid(Base):
    """供应商投标"""
    __tablename__ = "sourcing_bids"

    id = Column(Integer, primary_key=True, index=True)
    sourcing_id = Column(Integer, ForeignKey("sourcing_projects.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    round_number = Column(Integer, default=1)  # 报价轮次
    bid_data = Column(Text)                     # 报价数据 (JSON, 加密存储)
    technical_proposal = Column(Text)           # 技术方案摘要
    attachment_urls = Column(Text, default="[]")  # 附件URL列表
    total_amount = Column(Float, nullable=True)
    delivery_days = Column(Integer, nullable=True)  # 交期(天)
    payment_terms = Column(String(200))         # 付款条款
    is_opened = Column(Integer, default=0)     # 是否已开标(0=否,1=是)
    submitted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    sourcing = relationship("SourcingProject")
    supplier = relationship("Supplier")


class SourcingAward(Base):
    """寻源授标结果"""
    __tablename__ = "sourcing_awards"

    id = Column(Integer, primary_key=True, index=True)
    sourcing_id = Column(Integer, ForeignKey("sourcing_projects.id"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    is_winner = Column(Integer, default=1)    # 1=中标, 0=未中标
    awarded_amount = Column(Float)
    rejection_reason = Column(String(500))     # 落标原因(可选)
    notified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    sourcing = relationship("SourcingProject")
    supplier = relationship("Supplier")


class ContractTemplate(Base):
    """合同模板"""
    __tablename__ = "contract_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    applicable_categories = Column(String(500))  # 适用品类
    content = Column(Text, nullable=False)     # 模板内容(富文本)
    variables = Column(Text, default="[]")     # 变量占位符列表
    is_active = Column(Integer, default=1)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ContractStatus(str, enum.Enum):
    DRAFT = "draft"
    RECEIVED = "received"               # 草案已查收
    PENDING_FEEDBACK = "pending_feedback"  # 待反馈
    PENDING_SIGN = "pending_sign"       # 待签署
    SIGNED = "signed"                   # 已签署
    ACTIVE = "active"                   # 已生效
    EXPIRED = "expired"                 # 已到期
    TERMINATED = "terminated"           # 已终止


class Contract(Base):
    """合同"""
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    contract_no = Column(String(50), unique=True, nullable=False)
    sourcing_id = Column(Integer, ForeignKey("sourcing_projects.id"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("contract_templates.id"), nullable=True)
    contract_name = Column(String(200), nullable=False)
    contract_amount = Column(Float, nullable=True)
    content = Column(Text)                        # 合同正文
    status = Column(String(20), default="draft")
    # 签署流程
    sign_sequence = Column(String(20), default="supplier_first")  # supplier_first/buyer_first
    supplier_signed = Column(Integer, default=0)   # 0=未签, 1=已签
    supplier_signed_at = Column(DateTime, nullable=True)
    buyer_signed = Column(Integer, default=0)
    buyer_signed_at = Column(DateTime, nullable=True)
    signed_at = Column(DateTime, nullable=True)    # 双方签署完成时间
    # 履约节点
    effective_date = Column(DateTime, nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    supplier = relationship("Supplier")


class ContractComment(Base):
    """合同批注"""
    __tablename__ = "contract_comments"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    clause_id = Column(String(50))                # 条款编号
    party = Column(String(20), nullable=False)    # buyer/supplier
    comment = Column(Text, nullable=False)
    parent_id = Column(Integer, nullable=True)   # 回复上级批注
    resolved = Column(Integer, default=0)         # 是否已解决
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    contract = relationship("Contract")


# ==================== 公告栏模型 ====================

class AnnouncementType(str, enum.Enum):
    ANNOUNCEMENT = "announcement"  # 公告
    POLICY = "policy"              # 政策
    GUIDE = "guide"                # 操作指引


class Announcement(Base):
    """系统公告"""
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)          # 公告正文（支持富文本）
    announcement_type = Column(SQLEnum(AnnouncementType), default=AnnouncementType.ANNOUNCEMENT)
    priority = Column(Integer, default=0)            # 优先级: 0-普通, 1-重要, 2-紧急
    is_pinned = Column(Integer, default=0)           # 是否置顶
    attachments = Column(Text, default="[]")        # 附件 JSON: [{name, url}]
    published_by = Column(String(100))               # 发布人
    published_at = Column(DateTime, default=datetime.utcnow)
    valid_from = Column(DateTime, default=datetime.utcnow)  # 生效时间
    valid_until = Column(DateTime, nullable=True)   # 失效时间（可选）
    view_count = Column(Integer, default=0)          # 阅读次数
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AnnouncementRead(Base):
    """公告阅读记录"""
    __tablename__ = "announcement_reads"

    id = Column(Integer, primary_key=True, index=True)
    announcement_id = Column(Integer, ForeignKey("announcements.id"), nullable=False)
    user_id = Column(Integer, nullable=False)        # 阅读者用户ID
    read_at = Column(DateTime, default=datetime.utcnow)

    announcement = relationship("Announcement")


# ==================== Phase 3: 预测与订单执行模型 ====================

class ForecastStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CONFIRMED = "confirmed"
    EXPIRED = "expired"


class PurchaseForecast(Base):
    """采购预测"""
    __tablename__ = "purchase_forecasts"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    forecast_period = Column(String(50), nullable=False)  # 年/季度/月
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    items_data = Column(Text, default="[]")       # 预测明细 JSON: [{material_id, material_name, quantity, expected_month}]
    status = Column(SQLEnum(ForecastStatus), default=ForecastStatus.DRAFT)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)

    supplier = relationship("Supplier")


class ForecastResponse(Base):
    """供应商产能响应"""
    __tablename__ = "forecast_responses"

    id = Column(Integer, primary_key=True, index=True)
    forecast_id = Column(Integer, ForeignKey("purchase_forecasts.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    response_data = Column(Text, default="[]")   # 响应明细 JSON: [{material_id, committed_qty, committed_date, risk_level}]
    risk_summary = Column(Text)                   # 风险说明
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    forecast = relationship("PurchaseForecast")
    supplier = relationship("Supplier")


class DeliverySchedule(Base):
    """要货计划"""
    __tablename__ = "delivery_schedules"

    id = Column(Integer, primary_key=True, index=True)
    po_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    schedule_type = Column(String(20), default="weekly")  # weekly/daily
    required_date = Column(DateTime, nullable=False)
    items_data = Column(Text, default="[]")     # 明细 JSON
    status = Column(String(20), default="pending")  # pending/confirmed/adjusted
    supplier_confirmed = Column(Integer, default=0)
    confirmed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    supplier = relationship("Supplier")


class ASNStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"      # 已提交待确认
    CONFIRMED = "confirmed"     # 采购方已确认
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"


class ASN(Base):
    """提前发货通知 (ASN)"""
    __tablename__ = "asn"

    id = Column(Integer, primary_key=True, index=True)
    asn_no = Column(String(50), unique=True, nullable=False)
    schedule_id = Column(Integer, ForeignKey("delivery_schedules.id"), nullable=True)
    po_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    actual_ship_date = Column(DateTime, nullable=True)
    carrier_name = Column(String(200))
    carrier_contact = Column(String(100))
    tracking_no = Column(String(100))
    items_data = Column(Text, default="[]")     # 发货明细 JSON: [{material_id, qty, batch_no, production_date}]
    packing_list_url = Column(String(500))       # 装箱单URL
    status = Column(SQLEnum(ASNStatus), default=ASNStatus.DRAFT)
    confirmed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    supplier = relationship("Supplier")


class Receipt(Base):
    """入库单"""
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)
    receipt_no = Column(String(50), unique=True, nullable=False)
    asn_id = Column(Integer, ForeignKey("asn.id"), nullable=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=True)
    status = Column(String(20), default="pending")  # pending/qualified/unqualified
    total_quantity = Column(Float, default=0)
    qualified_quantity = Column(Float, default=0)
    unqualified_quantity = Column(Float, default=0)
    inspector = Column(String(100))
    inspected_at = Column(DateTime, nullable=True)
    remarks = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    supplier = relationship("Supplier")
    warehouse = relationship("Warehouse")
    items_rel = relationship("ReceiptItem", back_populates="receipt")


class ReceiptItem(Base):
    """入库单明细"""
    __tablename__ = "receipt_items"

    id = Column(Integer, primary_key=True, index=True)
    receipt_id = Column(Integer, ForeignKey("receipts.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=True)
    material_name = Column(String(200))
    quantity = Column(Float, default=0)
    unit = Column(String(20))
    batch_no = Column(String(50))
    production_date = Column(DateTime, nullable=True)
    quality_result = Column(String(20), default="qualified")  # qualified/unqualified
    warehouse_location = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    receipt = relationship("Receipt", back_populates="items_rel")


# ==================== Phase 4: 财务结算模型 ====================

class SettlementStatus(str, enum.Enum):
    PENDING_AUDIT = "pending_audit"
    CONFIRMED = "confirmed"
    DISPUTED = "disputed"
    CLOSED = "closed"


class SettlementStatement(Base):
    """结算单"""
    __tablename__ = "settlement_statements"

    id = Column(Integer, primary_key=True, index=True)
    statement_no = Column(String(50), unique=True, nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    settlement_period = Column(String(50), nullable=False)  # 结算期间
    period_start = Column(DateTime, nullable=True)  # 结算开始日期
    period_end = Column(DateTime, nullable=True)  # 结算结束日期
    receipt_ids = Column(Text, default="[]")   # 关联收货单ID列表
    total_amount = Column(Float, nullable=False)
    adjusted_amount = Column(Float, nullable=True)  # 调整后金额
    paid_amount = Column(Float, default=0)  # 已付金额
    status = Column(String(20), default="draft")  # draft/pending_audit/confirmed/paid/closed
    dispute_reason = Column(Text)
    remarks = Column(Text)  # 备注
    audited_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    audited_at = Column(DateTime, nullable=True)
    confirmed_by = Column(String(100), nullable=True)  # 确认人（供应商名称）
    confirmed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    supplier = relationship("Supplier")


class InvoiceStatus(str, enum.Enum):
    CREATED = "created"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"


class Invoice(Base):
    """发票"""
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_no = Column(String(50), unique=True, nullable=False)
    statement_id = Column(Integer, ForeignKey("settlement_statements.id"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    invoice_type = Column(String(20), default="VAT_SPECIAL")  # VAT_SPECIAL=专票/VAT_NORMAL=普票
    amount = Column(Float, nullable=False)
    tax_amount = Column(Float, nullable=True)
    tax_rate = Column(Float, default=0.13)
    invoice_date = Column(DateTime, nullable=True)
    invoice_image_url = Column(String(500))
    # 三单匹配
    match_status = Column(String(20), default="pending")  # pending/matched/amount_diff/quantity_diff/unmatched
    match_details = Column(Text, default="{}")
    # 审批
    status = Column(String(20), default="created")  # created/pending_approval/approved/rejected/verified/issued
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(String(500))
    remarks = Column(Text)  # 备注
    created_at = Column(DateTime, default=datetime.utcnow)

    supplier = relationship("Supplier")


class PaymentStatus(str, enum.Enum):
    APPLIED = "applied"           # 付款申请已提交
    FINANCE_APPROVED = "finance_approved"  # 财务已审批
    PAID = "paid"                 # 银行已支付
    RECEIVED = "received"         # 供应商已到账


class Payment(Base):
    """付款记录"""
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    payment_no = Column(String(50), unique=True, nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    statement_id = Column(Integer, ForeignKey("settlement_statements.id"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(String(50))   # bank_transfer/credit/other
    expected_date = Column(DateTime, nullable=True)
    actual_date = Column(DateTime, nullable=True)
    status = Column(String(20), default="applied")  # applied/finance_approved/paid/received
    pre_payment = Column(Integer, default=0)  # 是否预付款
    remarks = Column(Text)  # 备注
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    supplier = relationship("Supplier")


# 占位: 用户表 (简化版, 仅用于外键引用)
class User(Base):
    """系统用户 (简化版, 仅用于外键)"""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(100))
    role = Column(String(20), default="buyer")  # buyer/supplier_admin
    created_at = Column(DateTime, default=datetime.utcnow)
