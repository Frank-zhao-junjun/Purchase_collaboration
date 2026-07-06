# SAP S/4HANA 集成层 — 权威参考手册

> **单一信息源（Single Source of Truth）**：本文件汇总 SAP 集成层实现所需的全部权威数据，供 SDD implementer subagent 直接引用。
>
> **数据三重验证**：URS 理论值 → 真实租户实测数据 → SAP 官方 API 目录标准命名
>
> | 项 | 值 |
> |----|-----|
> | 生成日期 | 2026-07-06 |
> | 实测来源 | `D:\AI\ES-MCP-Server\Probe_Latest.json`（2026-06-22 探测，33 端点 24 OK / 9 403） |
> | 凭证来源 | `D:\AI\采购协同\user.txt`（已 gitignore，禁止提交） |
> | 官方目录 | https://api.sap.com/products/SAPS4HANACLOUD/apis/all |

---

## 0. 部署模型与集成架构（必读）

### 0.1 部署模型确认

| 项 | 值 |
|----|-----|
| **产品** | SAP S/4HANA Cloud, **Public Edition**（公有云版） |
| **租户 URL** | `REDACTED-SAP-TENANT.example.com` |
| **判定依据** | 域名 `REDACTED-SAP-TENANT-PATTERN` 为 SAP 公有云多租户域名；`-api` 后缀为 API 端点 |
| **Client** | `100` |
| **通信用户** | `REDACTED_SAP_COMM_USER`（通过 Communication Arrangement 授权） |

> ⚠️ **这是公有云，不是本地部署（On-Premise）**。两者的集成方式有本质区别，URS 原稿按本地部署写的 RFC/BAPI 出站方案在公有云下**不成立**，必须改为 OData 写操作。

### 0.2 公有云 vs 本地部署 集成方式对比

| 维度 | 本地部署 (On-Premise) | 公有云 (Public Cloud) ← 本项目 |
|------|----------------------|------------------------------|
| API 主协议 | RFC/BAPI + OData + IDoc | **OData V2/V4 + SOAP**（无直接 RFC） |
| 写操作（出站） | `BAPI_PO_CHANGE` 等 RFC 函数 | **OData PATCH/POST**（通信场景授权） |
| 事务码（ME22N/MIRO） | 客户可直接用 | 客户不可用，仅通过 API |
| 数据库表（EKKO 等） | 可直连读取 | 不可直连，仅通过 OData Entity |
| 访问治理 | 自定义权限对象 `S_RFC` | **Communication Arrangement**（`SAP_COM_xxxx`） |
| 连接方式 | RFC 库 / 直连 | HTTPS + Basic/OAuth + Communication User |

### 0.3 公有云通信场景（Communication Scenario）授权模型

公有云下**所有 API 访问（读 + 写）**都通过 Communication Arrangement 治理：

1. 每个 `SAP_COM_xxxx` 通信场景定义可用的 OData 服务 + 允许的操作（READ / CREATE / UPDATE / DELETE）
2. 通信用户 `REDACTED_SAP_COMM_USER` 通过 Arrangement 获得授权
3. **读权限 ≠ 写权限**：当前实测的 24 个 OK 端点仅验证了 READ，写操作（CREATE/UPDATE）需对应 Arrangement 单独开通

### 0.4 出站场景接口方案修正（RFC → OData）

| 场景 | URS 原方案（本地部署，❌ 公有云不适用） | 公有云正确方案（✅ OData） | 通信场景 | 实测读 | 写权限 |
|------|---------------------------------------|--------------------------|---------|--------|--------|
| INT-03 订单确认回传 | RFC `BAPI_PO_CHANGE`（ME22N） | OData V4 **PATCH** `api_purchaseorder_2/PurchaseOrder`（更新供应商确认字段） | SAP_COM_0053 | ✅ 7 entity OK | ⚠️ 待验证 |
| INT-11 发票校验回传 | RFC `BAPI_INCOMINGINVOICE_CREATE`（MIRO） | OData V2 **POST** `API_SUPPLIERINVOICE_PROCESS_SRV/A_SupplierInvoice`（创建发票校验） | legacy V2 | ✅ 3 entity OK | ⚠️ 待验证 |
| INT-06 要货确认回传 | OData UPDATE（本就正确） | OData **UPDATE** `API_PURCHASING_SCHEDULE_AGREEMENT_SRV`（更新计划行确认） | SAP_COM_0103 | ⚠️ 未探测 | ⚠️ 未探测 |

> **说明**：公有云下 `BAPI_PO_CHANGE` / `BAPI_INCOMINGINVOICE_CREATE` 等 RFC 函数不可直接调用。采购订单确认通过 OData V4 PATCH 更新 `PurchaseOrder` 的供应商确认相关字段；发票校验通过 OData V2 POST 创建 `A_SupplierInvoice` 记录（等价于 MIRO 过账）。

---
## 1. 真实租户连接配置

| 配置项 | 值 | 说明 |
|--------|-----|------|
| `SAP_BASE_URL` | `https://REDACTED-SAP-TENANT.example.com` | SAP API 根地址 |
| `SAP_CLIENT` | `100` | `sap-client` 查询参数 |
| `SAP_COMM_USER` | `REDACTED_SAP_COMM_USER` | 通信用户（无密码，密码在 user.txt） |
| `SAP_CREDENTIALS_FILE` | `./user.txt` | 凭证文件路径（本地，已 gitignore） |
| 认证方式 | Basic Auth | `Authorization: Basic base64(REDACTED_SAP_COMM_USER:<password>)` |
| 必带请求头 | `Accept: application/json` | — |
| 必带查询参数 | `$format=json&sap-client=100` | — |
| OData V2 路径前缀 | `/sap/opu/odata/sap/` | — |
| OData V4 路径前缀 | `/sap/opu/odata4/sap/.../srvd_a2x/sap/<name>/<ver>/` | — |

### 后端配置项（待加入 `backend/app/config.py`）

```python
# SAP S/4HANA 集成配置
SAP_BASE_URL: str = "https://REDACTED-SAP-TENANT.example.com"
SAP_CLIENT: str = "100"
SAP_COMM_USER: str = "REDACTED_SAP_COMM_USER"
SAP_COMM_PASSWORD: str = ""  # 从 user.txt 读取，不硬编码
SAP_CREDENTIALS_FILE: str = "./user.txt"
SAP_ODATA_V2_PREFIX: str = "/sap/opu/odata/sap/"
SAP_ODATA_V4_PREFIX: str = "/sap/opu/odata4/sap/"
SAP_REQUEST_HEADERS: dict = {"Accept": "application/json"}
SAP_REQUEST_PARAMS: dict = {"$format": "json", "sap-client": "100"}
```

---

## 2. 集成场景总览（15 场景 + 6 管理需求）

| 场景 | 关联 US | 数据对象 | 方向 | SAP 模块 | 同步触发 | 优先级 | 实测状态 |
|------|---------|---------|------|---------|---------|--------|---------|
| INT-01 | US-301 | 采购预测 | 入站 | PP/MDP | 定时拉取 (每 4h) | P0 | ⚠️ 未探测 |
| INT-02 | US-303 | 采购订单 | 入站 | MM/PUR | 事件推送 + 定时补拉 | P0 | ✅ OK |
| INT-03 | US-303 | 订单确认/拒绝结果 | 出站 | MM/PUR | 平台事件触发 | P0 | ⚠️ RFC 待验证 |
| INT-04 | US-304 | 订单变更/关闭 | 入站 | MM/PUR | 事件推送 | P0 | ✅ OK |
| INT-05 | US-305 | 要货计划 | 入站 | MM/PUR | 定时拉取 (每 1h) | P0 | ⚠️ 未探测 |
| INT-06 | US-306 | 要货计划确认/调整 | 出站 | MM/PUR | 平台事件触发 | P1 | ⚠️ 待验证 |
| INT-07 | US-310 | 收货单 | 入站 | MM/IM | 事件推送 | P0 | ✅ OK |
| INT-08 | US-310 | 质检结果 | 入站 | QM | 事件推送 | P0 | ⚠️ 未探测 |
| INT-09 | US-401 | 已收货未结算明细 | 入站 | MM/FI | 定时拉取 (每 1h) | P0 | ✅ 替代方案 OK |
| INT-10 | US-403 | 财务主数据 | 入站 | FI/MDM | 定时拉取 (每日) | P1 | ❌ 403 用替代 |
| INT-11 | US-403 | 发票校验回传 (MIRO) | 出站 | FI | 平台事件触发 | P1 | ⚠️ RFC 待验证 |
| INT-12 | US-405 | 付款状态 | 入站 | FI | 事件推送 | P0 | ⚠️ 未探测 |
| INT-13 | US-108 | 供应商主数据 | 入站 | MDM | 定时拉取 (每日) | P1 | ✅ OK |
| INT-14 | US-302 | 采购预测基础数据 | 入站 | PP/MDP | 随 INT-01 同步 | P1 | ⚠️ 随 INT-01 |
| INT-15 | 通用 | 物料主数据 | 入站 | MDM | 定时拉取 (每日) | P1 | ✅ OK |

---

## 3. 场景 ↔ SAP 接口 ↔ 平台 API 映射

### 3.1 入站同步（ERP → 平台）

| 场景 | SAP 实测接口（通信场景 / 状态） | 平台目标实体 | 平台既有 API |
|------|-------------------------------|-------------|-------------|
| INT-01 采购预测 | ⚠️ `API_PLANNED_ORDERS`（未探测）；替代：`API_PURCHASEREQ_PROCESS_SRV`（SAP_COM_0102，未探测） | PurchaseForecast | `POST /collaboration/forecasts`、`POST /collaboration/forecasts/{id}/publish`、`GET /collaboration/forecasts` |
| INT-02 采购订单 | ✅ V4 `api_purchaseorder_2`（SAP_COM_0053，7 entity 全 OK）；✅ V2 `API_PURCHASEORDER_PROCESS_SRV/A_PurchaseOrder`（legacy OK） | PurchaseOrder + OrderLineItem | `POST /purchase-orders/`、`GET /purchase-orders/`、`GET /purchase-orders/{id}` |
| INT-04 订单变更 | ✅ 同 INT-02（`api_purchaseorder_2` 读取变更版本） | PurchaseOrder | `PUT /purchase-orders/{id}`、`DELETE /purchase-orders/{id}` |
| INT-05 要货计划 | ⚠️ `API_PURCHASING_SCHEDULE_AGREEMENT_SRV`（SAP_COM_0103，未探测） | DeliverySchedule | `POST /collaboration/delivery-schedules`、`GET /collaboration/delivery-schedules` |
| INT-07 收货单 | ✅ `API_MATERIAL_DOCUMENT_SRV/A_MaterialDocumentHeader`（SAP_COM_0108，OK） | Receipt | `POST /logistics/receipts/`、`GET /logistics/receipts/`、`GET /logistics/receipts/{id}` |
| INT-08 质检结果 | ⚠️ `API_INSPECTIONLOT_SRV`（未探测）；或从物料凭证推断 | QualityInspection | `POST /inspections/`（核实是否内嵌于 logistics） |
| INT-09 结算明细 | ✅ `API_SUPPLIERINVOICE_PROCESS_SRV/A_SuplrInvcItemPurOrdRef`（V2 OK）按 PO 关联查询 | 结算可选明细 | `GET /financial/statements/` |
| INT-12 付款状态 | ⚠️ `API_JOURNALENTRY_SRV`（未探测）；过渡期从发票付款状态推断 | Payment | `POST /financial/payments/`、`GET /financial/payments/`、`GET /financial/payments/{id}` |
| INT-13 供应商主数据 | ✅ `API_BUSINESS_PARTNER/A_Supplier` + `A_SupplierCompany`（SAP_COM_0008，均 OK） | Supplier (sap_vendor_code) | `GET /suppliers/`、`PUT /suppliers/{id}` |
| INT-14 预测基础数据 | 随 INT-01 同步 | 预测维度数据 | `GET /collaboration/forecasts/{id}/responses`、`POST /collaboration/forecasts/{id}/responses` |
| INT-15 物料主数据 | ✅ V2 `API_PRODUCT_SRV/A_Product`（OK）；✅ V4 `api_product/.../Product`（OK）；✅ 物料组 `api_productgroup_2`（OK） | Material (sap_material_code) | `GET /materials/`、`POST /materials/`、`PUT /materials/{id}` |

### 3.2 INT-10 财务主数据（SAP_COM_0087 全 403，用替代方案）

| 需求 | 原计划接口 | 实测 | 替代 API（已 OK） |
|------|-----------|------|------------------|
| 公司代码 | `api_companycode` | ❌ 403 | `A_SupplierCompany.CompanyCodeName`（SAP_COM_0008） |
| 付款条件 | `api_paymentterms` | ❌ 403 | 从 `PurchaseOrder.PaymentTerms`（SAP_COM_0053）读取 |
| 工厂 | `api_plant` | ❌ 403 | 从 `PurchaseOrderItem.Plant` 读取 |
| 采购组织 | `api_purchasingorganization` | ❌ 403 | 从 `PurchaseOrder.PurchasingOrganization` 读取 |

### 3.3 出站回传（平台 → ERP）

| 场景 | 触发事件（平台 API） | SAP 回传接口 | 实测 | 幂等键 |
|------|---------------------|-------------|------|--------|
| INT-03 订单确认/拒绝/异议 | `POST /purchase-orders/{id}/supplier-confirm`<br>`POST /purchase-orders/{id}/supplier-reject`<br>`POST /purchase-orders/{id}/supplier-objection`<br>（供应商端：`POST /supplier-portal/orders/{id}/confirm`） | RFC `BAPI_PO_CHANGE`（ME22N） | ⚠️ RFC 待验证 | 平台订单号 + 操作类型 |
| INT-06 要货计划确认/调整 | `POST /collaboration/delivery-schedules/{id}/supplier-confirm`<br>`POST /supplier-portal/delivery-schedules/{id}/confirm` | OData `API_PURCHASING_SCHEDULE_AGREEMENT_SRV` UPDATE | ⚠️ 待验证 | 计划协议号 + 行项目 + 操作类型 |
| INT-11 发票校验 MIRO | `POST /financial/invoices/{id}/approve` | RFC `BAPI_INCOMINGINVOICE_CREATE`（MIRO） | ⚠️ RFC 待验证；读取侧 `API_SUPPLIERINVOICE_PROCESS_SRV`（V2 OK） | 发票号（不可重复过账） |

---

## 4. SAP 实测端点完整清单（33 个）

### 4.1 ✅ 可用端点（24 个 OK）

#### SAP 上游（14 个全 OK）

| # | 接口名称 | 通信场景 | 协议 | Entity / 路径 |
|---|----------|---------|------|--------------|
| 1 | 产品主数据 V2 | SAP_COM_0009 | OData V2 | `API_PRODUCT_SRV/A_Product` |
| 2 | 客户主数据 V2 | SAP_COM_0008 | OData V2 | `API_BUSINESS_PARTNER/A_Customer` |
| 3 | 销售订单 V4 | SAP_COM_0109 | OData V4 | `api_salesorder/.../SalesOrder` |
| 4 | 生产订单 V4 | SAP_COM_0104 | OData V4 | `api_productionorder/.../ProductionOrder` |
| 5 | 外向交货 V2 | SAP_COM_0106 | OData V2 | `API_OUTBOUND_DELIVERY_SRV;v=0002/A_OutbDeliveryHeader` |
| 6 | 开票 V2 | SAP_COM_0124 | OData V2 | `API_BILLING_DOCUMENT_SRV/A_BillingDocument` |
| 7 | 物料库存 V2 | SAP_COM_0164 | OData V2 | `API_MATERIAL_STOCK_SRV/A_MatlStkInAcctMod` |
| 8 | 采购订单 V2 | legacy | OData V2 | `API_PURCHASEORDER_PROCESS_SRV/A_PurchaseOrder` |
| 9 | 产品主数据 V4 | SAP_COM_0009 | OData V4 | `api_product/.../Product` |
| 10 | 物料组 V4 | SAP_COM_0009 | OData V4 | `api_productgroup_2/.../ProductGroup` |
| 11 | 供应商 V2 | SAP_COM_0008 | OData V2 | `API_BUSINESS_PARTNER/A_Supplier` |
| 12 | 供应商公司 V2 | SAP_COM_0008 | OData V2 | `API_BUSINESS_PARTNER/A_SupplierCompany` |
| 13 | 物料凭证 V2 | SAP_COM_0108 | OData V2 | `API_MATERIAL_DOCUMENT_SRV/A_MaterialDocumentHeader` |
| 14 | 成本中心 V4 | SAP_COM_0008 | OData V4 | `api_cost_center/.../A_CostCenter_2` |

#### EPC 采购（7 个全 OK，SAP_COM_0053，V4）

服务根：`/sap/opu/odata4/sap/api_purchaseorder_2/srvd_a2x/sap/purchaseorder/0001/`

| # | Entity Set | 用途 |
|---|------------|------|
| 15 | `PurchaseOrder` | 采购订单抬头 |
| 16 | `PurchaseOrderItem` | 行项目 |
| 17 | `PurchaseOrderScheduleLine` | 计划行（交货日期） |
| 18 | `PurOrderItemPricingElement` | 行定价（税） |
| 19 | `PurchaseOrderNote` | 抬头备注 |
| 20 | `PurchaseOrderItemNote` | 行备注 |
| 21 | `POSubcontractingComponent` | 委外组件 |

#### EPC 应付 V2（3 个 OK，推荐使用）

服务：`API_SUPPLIERINVOICE_PROCESS_SRV`

| # | 操作 | URL 模式 |
|---|------|----------|
| 22 | 列表 | `.../A_SupplierInvoice?$top=50&$format=json&sap-client=100` |
| 23 | 单张 | `.../A_SupplierInvoice(SupplierInvoice=''{Invoice}'',FiscalYear=''{Year}'')?$format=json&sap-client=100` |
| 24 | 行(PO参考) | `.../A_SuplrInvcItemPurOrdRef?$filter=SupplierInvoice eq ''{Invoice}'' and FiscalYear eq ''{Year}''&$format=json&sap-client=100` |

**已验证示例**：发票 `5105600101` / 年度 `2025`，行项目关联 PO `4500000000/10`，金额 12000 CNY。

### 4.2 ❌ 不可用端点（9 个 403）

#### EPC 应付 V4（3 个 403，需开通 SAP_COM_0054）

| # | Entity | 状态 |
|---|--------|------|
| 25 | `SupplierInvoice`（V4） | FAIL(403) |
| 26 | `SuplrInvcItemPurOrdRef`（V4） | FAIL(403) |
| 27 | `SupplierInvoiceTax`（V4） | FAIL(403) |

#### 主数据 SAP_COM_0087（6 个全 403，需开通 Scope Item 1YB）

| # | 接口名称 | Entity | API 服务 |
|---|----------|--------|----------|
| 28 | 付款条件 V4 | `PaymentTerms` | `api_paymentterms` |
| 29 | 工厂 V4 | `Plant` | `api_plant` |
| 30 | 采购组织 V4 | `A_PurchasingOrganization` | `api_purchasingorganization` |
| 31 | 采购组 V4 | `A_PurchasingGroup` | `api_purchasinggroup` |
| 32 | 公司代码 V4 | `CompanyCode` | `api_companycode` |
| 33 | 库存地点 V4 | `StorageLocation` | `api_storagelocation` |

### 4.3 ⚠️ 未探测端点（URS 需要，不在 33 端点中）

| 场景 | 官方服务名 | CDS View | 通信场景 | 建议 |
|------|-----------|----------|---------|------|
| INT-01 采购预测 | `API_PLANNED_ORDERS` | I_PlannedOrder | — | 探测或改用采购申请 `API_PURCHASEREQ_PROCESS_SRV`（SAP_COM_0102） |
| INT-05 要货计划 | `API_PURCHASING_SCHEDULE_AGREEMENT_SRV` | I_PurchasingSchedgAgrmt | SAP_COM_0103 | 需探测 |
| INT-08 质检结果 | `API_INSPECTIONLOT_SRV` | I_InspectionLot | — | 需探测，或从物料凭证推断 |
| INT-12 付款状态 | `API_JOURNALENTRY_SRV` | I_JournalEntry | — | 需探测，过渡期从发票付款状态推断 |
| INT-03/11 出站 RFC | `BAPI_PO_CHANGE` / `BAPI_INCOMINGINVOICE_CREATE` | — | — | 需 SAP Basis 配合单独验证 |

---

## 5. 服务名勘误（URS 错误 → 正确）

| 场景 | URS 原写法（错误） | 正确服务名 | 依据 |
|------|-------------------|-----------|------|
| INT-13 | `API_BUSINESS_PARTNER_SRV` | `API_BUSINESS_PARTNER` | 实测路径无 `_SRV` 后缀 |
| INT-02/04/09 | `API_PURCHASE_ORDER_PROCESS_SRV` | `API_PURCHASEORDER_PROCESS_SRV`（PURCHASEORDER 连写）；V4 推荐 `api_purchaseorder_2` | 实测 V2 路径 + V4 7 entity OK |

---

## 6. 字段映射

### 6.1 INT-02 采购订单（对齐 URS 12.3）

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

> **V4 字段名差异**：V4 `api_purchaseorder_2` 用 camelCase（`PurchaseOrder`、`Supplier`、`CompanyCode`、`PurchasingOrganization`、`PaymentTerms`），非 V2 的 `A_PurchaseOrder`。实现时需在 `field_mappings` 表配置 V2/V4 双映射。

### 6.2 供应商发票（INT-09/11）

| SAP 字段 | 平台字段 | 说明 |
|---------|---------|------|
| SupplierInvoice | invoice.sap_invoice_number | SAP 发票号 |
| FiscalYear | invoice.fiscal_year | 财年 |
| CompanyCode | invoice.company_code | 公司代码 |
| Supplier | invoice.supplier.sap_vendor_code | 供应商编号 |
| DocumentDate | invoice.document_date | 凭证日期 |
| PostingDate | invoice.posting_date | 过账日期 |
| InvoiceGrossAmount | invoice.gross_amount | 发票总额 |
| TaxAmount | invoice.tax_amount | 税额 |

---

## 7. 集成管理 API（新增，前缀 `/integration`）

| 方法 | 路径 | 功能 | 关联需求 |
|------|------|------|---------|
| GET | `/integration/monitor/overview` | 同步概览看板 | INT-M03-01 |
| GET | `/integration/monitor/connection` | ERP 连接状态（心跳探针） | INT-M03-03 |
| GET | `/integration/logs` | 同步日志列表 | INT-M01-02 |
| GET | `/integration/logs/{log_id}` | 同步日志详情 | INT-M01-04 |
| POST | `/integration/retry/{log_id}` | 手动重推单条 | INT-M02-03 |
| POST | `/integration/retry/batch` | 按场景批量重推 | INT-M02-04 |
| GET | `/integration/scenarios` | 场景配置列表 | INT-M05-01 |
| PUT | `/integration/scenarios/{scenario_code}` | 更新场景配置 | INT-M05-01/03 |
| GET | `/integration/field-mappings` | 字段映射配置列表 | INT-M04-01 |
| PUT | `/integration/field-mappings/{mapping_id}` | 更新字段映射（热加载） | INT-M04-03 |

---

## 8. 关键约束（实现时必须遵守）

1. **采购订单必须用 `api_purchaseorder_2`**（带 `_2`，V4 SAP_COM_0053），旧路径 `api_purchaseorder`（无 `_2`）会 403。
2. **供应商发票用 V2**（`API_SUPPLIERINVOICE_PROCESS_SRV`），V4（SAP_COM_0054）全部 403 需开通。
3. **主数据 SAP_COM_0087 全 403**，过渡期用替代方案（从采购订单/供应商公司读取）。
4. **幂等键**：入站 = `SAP 单据号 + 行项目号 + 最后变更时间戳`；出站 = `平台单据号 + 操作类型`。
5. **重试策略**：间隔 `30s → 2min → 10min → 30min`，最多 4 次。
6. **日志保留**：≥ 90 天，含场景编号/方向/SAP 单据号/平台单据号/同步时间/状态/错误信息。
7. **同步延迟阈值**：入站 15min / 出站 5min 超阈值告警；ERP 心跳探针每 60s 一次。
8. **平台不写回 ERP 业务数据**：出站仅回传「供应商协同结果」。
9. **不改业务逻辑**：集成层只替换数据来源，现有 67 条 US 烟测必须持续通过。
10. **ODataConnector 须同时支持 V2/V4** 两种路径模式。
11. **凭证安全**：密码从 `user.txt` 读取，不硬编码；`user.txt` 已 gitignore。

---

## 9. 文件索引

| 文件 | 用途 |
|------|------|
| `docs/URS-SAP-S4HANA-Integration.md` | 用户需求规格（已修正服务名） |
| `docs/INTEGRATION-API-MAP.md` | 接口对照表（三重验证） |
| `docs/superpowers/plans/2026-07-06-sap-s4hana-integration.md` | SDD 实现计划（6 Phase / 20 task） |
| `docs/RALPH-TODO.md` | Ralph-loop TODO（含集成层章节） |
| `Integration/README.md` | 本文件（权威参考手册） |
| `user.txt`（gitignore） | SAP 凭证（本地） |
| `D:\AI\ES-MCP-Server\Probe_Latest.json` | 实测端点数据（外部） |
| `D:\AI\ES-MCP-Server\docs\SAP接口连通性手册.md` | 连通性手册（外部） |