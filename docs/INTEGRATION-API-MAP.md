# 集成场景接口对照表（INT ↔ SAP ↔ 平台 API）

> 用途：SAP S/4HANA 集成层实现时，每个 INT 场景的 SAP 侧接口与平台侧 REST API 的完整对照。
> 数据来源：`docs/URS-SAP-S4HANA-Integration.md` 附录 + 后端 `backend/app/api/*.py` 路由提取。
> 生成日期：2026-07-06

---

## 一、入站同步（ERP → 平台）

平台侧 API 为集成层**写入数据**的目标实体对应的既有路由（集成层调用 service 层持久化，不直接暴露新路由）。

| 场景 | 关联 US | SAP 接口 | 方向 | 平台目标实体 | 平台既有 API（参考） |
|------|---------|---------|------|-------------|-------------------|
| INT-01 采购预测 | US-301 | OData `API_PLANNED_ORDERS` (I_PlannedOrder) READ | 入站 | PurchaseForecast | `POST /collaboration/forecasts`、`POST /collaboration/forecasts/{id}/publish`、`GET /collaboration/forecasts` |
| INT-02 采购订单 | US-303 | OData `API_PURCHASE_ORDER_PROCESS_SRV` (I_PurchaseOrder) READ | 入站 | PurchaseOrder + OrderLineItem | `POST /purchase-orders/`、`GET /purchase-orders/`、`GET /purchase-orders/{id}` |
| INT-03 订单确认回传 | US-303 | RFC `BAPI_PO_CHANGE` (ME22N) UPDATE | **出站** | — | 触发源：`POST /purchase-orders/{id}/supplier-confirm`、`/supplier-reject`、`/supplier-objection` |
| INT-04 订单变更/关闭 | US-304 | OData `API_PURCHASE_ORDER_PROCESS_SRV` (I_PurchaseOrder 变更版本) READ | 入站 | PurchaseOrder | `PUT /purchase-orders/{id}`、`DELETE /purchase-orders/{id}` |
| INT-05 要货计划 | US-305 | OData `API_PURCHASING_SCHEDULE_AGREEMENT_SRV` (I_PurchasingSchedgAgrmt) READ | 入站 | DeliverySchedule | `POST /collaboration/delivery-schedules`、`GET /collaboration/delivery-schedules` |
| INT-06 要货确认回传 | US-306 | OData `API_PURCHASING_SCHEDULE_AGREEMENT_SRV` UPDATE | **出站** | — | 触发源：`POST /collaboration/delivery-schedules/{id}/supplier-confirm`、`POST /supplier-portal/delivery-schedules/{id}/confirm` |
| INT-07 收货单 | US-310 | OData `API_MATERIAL_DOCUMENT_SRV` (I_MaterialDocument) READ | 入站 | Receipt | `POST /logistics/receipts/`、`GET /logistics/receipts/`、`GET /logistics/receipts/{id}` |
| INT-08 质检结果 | US-310 | OData `API_INSPECTIONLOT_SRV` (I_InspectionLot) READ | 入站 | QualityInspection | `POST /inspections/`（注：路由在 logistics/receipts 关联） |
| INT-09 已收货未结算明细 | US-401 | OData `API_PURCHASE_ORDER_PROCESS_SRV` (I_PurchaseOrderHistory) READ | 入站 | 结算可选明细 | `GET /financial/statements/`（供应商创建结算单时引用） |
| INT-10 财务主数据 | US-403 | OData（Vendor/CompanyCode）READ | 入站 | 财务主数据 | `GET /financial/statements/`、`GET /financial/invoices/`（引用） |
| INT-11 发票校验回传 | US-403 | RFC `BAPI_INCOMINGINVOICE_CREATE` (MIRO) CREATE | **出站** | — | 触发源：`POST /financial/invoices/{id}/approve` |
| INT-12 付款状态 | US-405 | OData `API_JOURNALENTRY_SRV` (I_JournalEntry) READ | 入站 | Payment | `POST /financial/payments/`、`GET /financial/payments/`、`GET /financial/payments/{id}` |
| INT-13 供应商主数据 | US-108 | OData `API_BUSINESS_PARTNER_SRV` (I_BusinessPartner) READ | 入站 | Supplier (sap_vendor_code) | `GET /suppliers/`、`PUT /suppliers/{id}` |
| INT-14 预测基础数据 | US-302 | 随 INT-01 同步 | 入站 | 预测维度数据 | `GET /collaboration/forecasts/{id}/responses`、`POST /collaboration/forecasts/{id}/responses` |
| INT-15 物料主数据 | 通用 | OData `API_PRODUCT_SRV` (I_Product) READ | 入站 | Material (sap_material_code) | `GET /materials/`、`POST /materials/`、`PUT /materials/{id}` |

---

## 二、出站回传（平台 → ERP）

出站场景由**平台既有业务路由的事件钩子**触发，集成层监听这些事件后调用 SAP RFC/OData 回传。

| 场景 | 关联 US | 触发事件（平台 API） | SAP 回传接口 | 幂等键 |
|------|---------|---------------------|-------------|--------|
| INT-03 订单确认/拒绝/异议 | US-303 | `POST /purchase-orders/{id}/supplier-confirm`<br>`POST /purchase-orders/{id}/supplier-reject`<br>`POST /purchase-orders/{id}/supplier-objection`<br>（供应商端：`POST /supplier-portal/orders/{id}/confirm`） | RFC `BAPI_PO_CHANGE` | 平台订单号 + 操作类型 |
| INT-06 要货计划确认/调整 | US-306 | `POST /collaboration/delivery-schedules/{id}/supplier-confirm`<br>`POST /supplier-portal/delivery-schedules/{id}/confirm` | OData `API_PURCHASING_SCHEDULE_AGREEMENT_SRV` UPDATE | 计划协议号 + 行项目 + 操作类型 |
| INT-11 发票校验 MIRO | US-403 | `POST /financial/invoices/{id}/approve` | RFC `BAPI_INCOMINGINVOICE_CREATE` | 发票号（不可重复过账） |

---

## 三、集成管理 API（新增，Phase 0.4 / Phase 4 实现）

集成层自身新增的管理路由，前缀 `/integration`：

| 方法 | 路径 | 功能 | 关联需求 |
|------|------|------|---------|
| GET | `/integration/monitor/overview` | 同步概览看板（各场景最近同步时间/成功率/积压数） | INT-M03-01 |
| GET | `/integration/monitor/connection` | ERP 连接状态（心跳探针） | INT-M03-03 |
| GET | `/integration/logs` | 同步日志列表（按场景/单据号/时间/状态检索） | INT-M01-02 |
| GET | `/integration/logs/{log_id}` | 同步日志详情（含请求/响应报文） | INT-M01-04 |
| POST | `/integration/retry/{log_id}` | 手动重推单条失败记录 | INT-M02-03 |
| POST | `/integration/retry/batch` | 按场景批量重推 | INT-M02-04 |
| GET | `/integration/scenarios` | 场景配置列表（含 enabled 开关） | INT-M05-01 |
| PUT | `/integration/scenarios/{scenario_code}` | 更新场景配置（启停/频率） | INT-M05-01/03 |
| GET | `/integration/field-mappings` | 字段映射配置列表 | INT-M04-01 |
| PUT | `/integration/field-mappings/{mapping_id}` | 更新字段映射（热加载） | INT-M04-03 |

---

## 四、SAP 侧接口完整清单

### 4.1 OData 服务（入站读取，10 个）

| 场景 | OData 服务名 | CDS View | 操作 |
|------|-------------|----------|------|
| INT-01 | API_PLANNED_ORDERS | I_PlannedOrder | READ |
| INT-02 | API_PURCHASE_ORDER_PROCESS_SRV | I_PurchaseOrder | READ |
| INT-04 | API_PURCHASE_ORDER_PROCESS_SRV | I_PurchaseOrder | READ (变更版本) |
| INT-05 | API_PURCHASING_SCHEDULE_AGREEMENT_SRV | I_PurchasingSchedgAgrmt | READ |
| INT-07 | API_MATERIAL_DOCUMENT_SRV | I_MaterialDocument | READ |
| INT-08 | API_INSPECTIONLOT_SRV | I_InspectionLot | READ |
| INT-09 | API_PURCHASE_ORDER_PROCESS_SRV | I_PurchaseOrderHistory | READ |
| INT-12 | API_JOURNALENTRY_SRV | I_JournalEntry | READ |
| INT-13 | API_BUSINESS_PARTNER_SRV | I_BusinessPartner | READ |
| INT-15 | API_PRODUCT_SRV | I_Product | READ |

### 4.2 RFC/BAPI（出站回传，2 个）

| 场景 | 函数模块 | 事务码 | 操作 |
|------|---------|--------|------|
| INT-03 | BAPI_PO_CHANGE | ME22N | UPDATE（确认字段） |
| INT-11 | BAPI_INCOMINGINVOICE_CREATE | MIRO | CREATE（发票校验） |

### 4.3 OData 出站更新（1 个）

| 场景 | OData 服务名 | 操作 |
|------|-------------|------|
| INT-06 | API_PURCHASING_SCHEDULE_AGREEMENT_SRV | UPDATE（计划行确认） |

---

## 五、字段映射（INT-02 采购订单示例，URS 12.3）

| SAP 字段 | 平台字段 | 说明 |
|---------|---------|------|
| EKKO-EBELN | purchase_order.sap_po_number | SAP 采购订单号 |
| EKKO-LIFNR | purchase_order.supplier.sap_vendor_code | SAP 供应商编号 |
| EKKO-BUKRS | purchase_order.company_code | 公司代码 |
| EKKO-EKORG | purchase_order.purchasing_org | 采购组织 |
| EKKO-ZTERM | purchase_order.payment_terms | 付款条件 |
| EKPO-EBELP | order_line_item.line_number | 行项目号 |
| EKPO-MATNR | order_line_item.material.sap_material_code | 物料编号 |
| EKPO-MENGE | order_line_item.quantity | 订单数量 |
| EKPO-MEINS | order_line_item.unit | 单位 |
| EKPO-NETPR | order_line_item.unit_price | 净价 |
| EKPO-EINDT | order_line_item.delivery_date | 交货日期 |
| EKPO-WERKS | order_line_item.plant | 工厂 |