"""API schemas"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class SupplierBase(BaseModel):
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    status: str = "active"
    rating: float = 5.0

class SupplierCreate(SupplierBase): pass
class SupplierUpdate(BaseModel):
    name: Optional[str] = None; contact_person: Optional[str] = None
    phone: Optional[str] = None; email: Optional[str] = None
    address: Optional[str] = None; status: Optional[str] = None; rating: Optional[float] = None

class SupplierResponse(SupplierBase):
    id: int; created_at: datetime; updated_at: datetime
    class Config: from_attributes = True

class MaterialBase(BaseModel):
    name: str; category: Optional[str] = None; unit: str = "吨"
    unit_price: float = 0.0; stock_quantity: float = 0.0
    reorder_point: float = 10.0; supplier_id: Optional[int] = None; origin: Optional[str] = None

class MaterialCreate(MaterialBase): pass
class MaterialUpdate(BaseModel):
    name: Optional[str] = None; category: Optional[str] = None; unit: Optional[str] = None
    unit_price: Optional[float] = None; stock_quantity: Optional[float] = None
    reorder_point: Optional[float] = None; supplier_id: Optional[int] = None; origin: Optional[str] = None

class MaterialResponse(MaterialBase):
    id: int; created_at: datetime; updated_at: datetime
    class Config: from_attributes = True

class ProductBase(BaseModel):
    name: str; brand: Optional[str] = None; category: Optional[str] = None
    abv: float = 53.0; specification: Optional[str] = None
    unit_price: float = 0.0; stock_quantity: int = 0
    status: str = "active"; description: Optional[str] = None

class ProductCreate(ProductBase): pass
class ProductUpdate(BaseModel):
    name: Optional[str] = None; brand: Optional[str] = None; category: Optional[str] = None
    abv: Optional[float] = None; specification: Optional[str] = None
    unit_price: Optional[float] = None; stock_quantity: Optional[int] = None
    status: Optional[str] = None; description: Optional[str] = None

class ProductResponse(ProductBase):
    id: int; created_at: datetime; updated_at: datetime
    class Config: from_attributes = True

class PurchaseOrderItemBase(BaseModel):
    material_id: int; quantity: float; unit_price: float; subtotal: float

class PurchaseOrderItemCreate(PurchaseOrderItemBase): pass

class PurchaseOrderItemResponse(PurchaseOrderItemBase):
    id: int
    class Config: from_attributes = True

class PurchaseOrderBase(BaseModel):
    supplier_id: int; expected_delivery_date: Optional[datetime] = None; notes: Optional[str] = None

class PurchaseOrderCreate(PurchaseOrderBase):
    items: List[PurchaseOrderItemCreate]

class PurchaseOrderUpdate(BaseModel):
    status: Optional[str] = None; expected_delivery_date: Optional[datetime] = None
    actual_delivery_date: Optional[datetime] = None; notes: Optional[str] = None

class PurchaseOrderResponse(PurchaseOrderBase):
    id: int; order_no: str; total_amount: float; status: str
    actual_delivery_date: Optional[datetime] = None; created_at: datetime; updated_at: datetime
    items: List[PurchaseOrderItemResponse] = []
    class Config: from_attributes = True

class SalesOrderBase(BaseModel):
    product_id: int; customer_name: str; customer_contact: Optional[str] = None
    quantity: int; unit_price: float; total_amount: float
    shipping_address: Optional[str] = None; expected_ship_date: Optional[datetime] = None; notes: Optional[str] = None

class SalesOrderCreate(SalesOrderBase): pass
class SalesOrderUpdate(BaseModel):
    status: Optional[str] = None; expected_ship_date: Optional[datetime] = None
    actual_ship_date: Optional[datetime] = None; notes: Optional[str] = None

class SalesOrderResponse(SalesOrderBase):
    id: int; order_no: str; status: str; actual_ship_date: Optional[datetime] = None
    created_at: datetime; updated_at: datetime
    class Config: from_attributes = True

class MaterialUsageBase(BaseModel):
    material_name: str; quantity: float

class MaterialUsageCreate(MaterialUsageBase): pass

class MaterialUsageResponse(MaterialUsageBase):
    id: int
    class Config: from_attributes = True

class ProductionRecordBase(BaseModel):
    product_id: int; batch_no: str; quantity: int; qualified_quantity: int = 0
    quality_rate: float = 0.0; operator: Optional[str] = None; notes: Optional[str] = None

class ProductionRecordCreate(ProductionRecordBase):
    material_usages: List[MaterialUsageCreate] = []

class ProductionRecordResponse(ProductionRecordBase):
    id: int; production_date: datetime; created_at: datetime
    material_usages: List[MaterialUsageResponse] = []
    class Config: from_attributes = True

class WarehouseBase(BaseModel):
    name: str; location: Optional[str] = None; capacity: int = 0
    current_stock: int = 0; manager: Optional[str] = None; status: str = "active"

class WarehouseCreate(WarehouseBase): pass
class WarehouseUpdate(BaseModel):
    name: Optional[str] = None; location: Optional[str] = None; capacity: Optional[int] = None
    current_stock: Optional[int] = None; manager: Optional[str] = None; status: Optional[str] = None

class WarehouseResponse(WarehouseBase):
    id: int; created_at: datetime
    class Config: from_attributes = True

class DashboardStats(BaseModel):
    total_products: int; total_suppliers: int; total_orders: int; total_revenue: float
    pending_orders: int; low_stock_materials: int; production_today: int


# ==================== Phase 1: 协同 Schema ====================

class SupplierExtendedBase(SupplierBase):
    origin_type: Optional[str] = "一般产区"
    main_category: Optional[str] = None
    annual_capacity: Optional[float] = 0.0
    cooperation_years: Optional[int] = 0
    quality_score: Optional[float] = 5.0
    delivery_score: Optional[float] = 5.0
    service_score: Optional[float] = 5.0
    qualifications: Optional[str] = "[]"

class SupplierExtendedCreate(SupplierExtendedBase): pass

class SupplierExtendedUpdate(BaseModel):
    name: Optional[str] = None; contact_person: Optional[str] = None
    phone: Optional[str] = None; email: Optional[str] = None
    address: Optional[str] = None; status: Optional[str] = None
    origin_type: Optional[str] = None; main_category: Optional[str] = None
    annual_capacity: Optional[float] = None; cooperation_years: Optional[int] = None
    quality_score: Optional[float] = None; delivery_score: Optional[float] = None
    service_score: Optional[float] = None; qualifications: Optional[str] = None

class SupplierExtendedResponse(SupplierExtendedBase):
    id: int; created_at: datetime; updated_at: datetime
    class Config: from_attributes = True


class PurchaseOrderExtendedResponse(PurchaseOrderResponse):
    supplier_confirmed_at: Optional[datetime] = None
    supplier_rejection_reason: Optional[str] = None
    created_by: Optional[str] = "系统"
    supplier_name: Optional[str] = None
    class Config: from_attributes = True


# PO 确认/拒绝请求
class POConfirmRequest(BaseModel):
    action: str  # "confirm" or "reject"
    rejection_reason: Optional[str] = None


# ASN 送货单 Schema
class ShipmentNoteItemBase(BaseModel):
    material_id: int
    material_name: Optional[str] = None
    quantity: float
    unit: str = "吨"
    batch_no: Optional[str] = None
    production_date: Optional[datetime] = None
    origin_location: Optional[str] = None
    quality_grade: Optional[str] = None
    package_count: Optional[int] = 1
    notes: Optional[str] = None

class ShipmentNoteItemCreate(ShipmentNoteItemBase): pass

class ShipmentNoteItemResponse(ShipmentNoteItemBase):
    id: int; created_at: datetime
    class Config: from_attributes = True


class ShipmentNoteBase(BaseModel):
    purchase_order_id: int
    carrier_name: Optional[str] = None
    tracking_no: Optional[str] = None
    vehicle_no: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    expected_arrival: Optional[datetime] = None
    shipping_address: Optional[str] = None
    receiving_warehouse: Optional[str] = None
    notes: Optional[str] = None

class ShipmentNoteCreate(ShipmentNoteBase):
    items: List[ShipmentNoteItemCreate] = []

class ShipmentNoteUpdate(BaseModel):
    status: Optional[str] = None
    carrier_name: Optional[str] = None
    tracking_no: Optional[str] = None
    vehicle_no: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    expected_arrival: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    notes: Optional[str] = None

class ShipmentNoteResponse(ShipmentNoteBase):
    id: int; shipment_no: str; supplier_id: int; status: str
    actual_arrival: Optional[datetime] = None
    total_quantity: Optional[float] = 0.0
    created_at: datetime; updated_at: datetime
    items: List[ShipmentNoteItemResponse] = []
    purchase_order_no: Optional[str] = None
    supplier_name: Optional[str] = None
    class Config: from_attributes = True


# 供应商门户待办统计
class SupplierTodoStats(BaseModel):
    pending_confirm_orders: int = 0   # 待确认订单
    pending_shipment_notes: int = 0   # 待发货
    in_transit_count: int = 0         # 运输中


# ==================== Phase 1: 供应商准入 Schemas ====================

class InvitationCreate(BaseModel):
    """创建邀请请求"""
    invited_supplier_name: str
    invited_email: str
    invited_contact_person: Optional[str] = None
    expiry_days: int = 7        # 有效期天数，默认7天
    notes: Optional[str] = None


class InvitationResponse(BaseModel):
    """邀请响应"""
    id: int
    invitation_code: str
    invited_supplier_name: str
    invited_email: str
    invited_contact_person: Optional[str] = None
    status: str
    expiry_date: datetime
    created_at: datetime
    notes: Optional[str] = None
    class Config: from_attributes = True


class InvitationValidateResponse(BaseModel):
    """验证邀请码响应"""
    valid: bool
    invitation_code: str
    invited_supplier_name: str
    invited_email: str
    expiry_date: datetime
    message: Optional[str] = None


class RegistrationCreate(BaseModel):
    """供应商注册请求"""
    invitation_code: Optional[str] = None
    company_name: str
    unified_credit_code: str
    contact_person: str
    contact_phone: str
    contact_email: Optional[str] = None
    address: Optional[str] = None
    main_categories: Optional[str] = None
    annual_capacity: Optional[float] = 0.0
    employee_count: Optional[int] = 0
    established_year: Optional[int] = None


class RegistrationResponse(BaseModel):
    """注册响应"""
    id: int
    company_name: str
    unified_credit_code: str
    contact_person: str
    contact_phone: str
    contact_email: Optional[str] = None
    status: str
    created_at: datetime
    class Config: from_attributes = True


class AuditRequest(BaseModel):
    """审核请求"""
    action: str        # approve/reject
    opinion: Optional[str] = None  # 审核意见


class CertificationCreate(BaseModel):
    """添加供应商资质"""
    cert_type: str    # 营业执照/生产许可证/质量体系认证/行业资质
    cert_name: str
    cert_no: Optional[str] = None
    issue_date: Optional[datetime] = None
    expiry_date: datetime
    cert_file_url: Optional[str] = None


class CertificationResponse(BaseModel):
    """资质响应"""
    id: int
    supplier_id: int
    cert_type: str
    cert_name: str
    cert_no: Optional[str] = None
    issue_date: Optional[datetime] = None
    expiry_date: datetime
    status: str
    days_until_expiry: Optional[int] = None
    created_at: datetime
    class Config: from_attributes = True


class SupplierAlertResponse(BaseModel):
    """供应商预警响应"""
    id: int
    supplier_id: int
    alert_type: str
    message: str
    days_before_expiry: Optional[int] = None
    is_read: int
    is_resolved: int
    created_at: datetime
    supplier_name: Optional[str] = None
    class Config: from_attributes = True
    pending_settlement: int = 0       # 待对账


# ==================== 采购预测 ====================

class ForecastItem(BaseModel):
    """预测明细项"""
    material_id: Optional[int] = None
    material_name: str
    quantity: float
    expected_month: Optional[str] = None
    notes: Optional[str] = None

class PurchaseForecastResponse(BaseModel):
    """采购预测响应"""
    id: int
    supplier_id: int
    supplier_name: Optional[str] = None
    forecast_period: str
    period_start: datetime
    period_end: datetime
    items_data: str = "[]"
    status: str = "draft"
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    class Config: from_attributes = True
# ==================== 采购预测 ====================

class ForecastItem(BaseModel):
    """预测明细项"""
    material_id: Optional[int] = None
    material_name: str
    quantity: float
    expected_month: Optional[str] = None
    notes: Optional[str] = None

class PurchaseForecastResponse(BaseModel):
    """采购预测响应"""
    id: int
    supplier_id: int
    supplier_name: Optional[str] = None
    forecast_period: str
    period_start: datetime
    period_end: datetime
    items_data: str = "[]"
    status: str = "draft"
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    class Config: from_attributes = True
