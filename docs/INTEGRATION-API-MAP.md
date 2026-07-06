# 集成场景接口对照表（INT ↔ SAP ↔ 平台 API）

> 用途：SAP S/4HANA 集成层实现时，每个 INT 场景的 SAP 侧接口与平台侧 REST API 的完整对照。
> **数据来源**：
> - SAP 侧实测：`D:\AI\ES-MCP-Server\docs\SAP接口连通性手册.md` + `Probe_Latest.json`（真实租户 `REDACTED-SAP-TENANT.example.com` / client 100 / 用户 `REDACTED_SAP_COMM_USER`，2026-06-22 探测，33 端点 24 OK / 9 403）
> - 平台侧：后端 `backend/app/api/*.py` 路由提取
> - URS 理论值：`docs/URS-SAP-S4HANA-Integration.md` 附录
> 更新日期：2026-07-06（基于实测数据修订）

---

## 〇、真实租户连接配置（来自 user.txt，Demo + 联调用）

> ⚠️ 凭证文件 `user.txt` 已加入 `.gitignore`，禁止提交。密码仅存于本地 `user.txt`，不写入代码或文档。

| 配置项 | 值 | 说明 |
|--------|-----|------|
| `SAP_BASE_URL` | `https://REDACTED-SAP-TENANT.example.com` | SAP API 根地址 |
| `SAP_CLIENT` | `100` | `sap-client` 查询参数 |
| `SAP_CREDENTIALS_FILE` | `./user.txt` | 凭证文件路径（本地，已 gitignore） |
| `SAP_COMM_USER` | `REDACTED_SAP_COMM_USER` | 通信用户（无密码，密码在 user.txt） |
| 认证方式 | Basic Auth | `Authorization: Basic base64(REDACTED_SAP_COMM_USER:<password>)` |
| 必带请求头 | `Accept: application/json` | — |
| 必带查询参数 | `$format=json&sap-client=100` | — |

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
## 〇、真实租户关键约束（必读）

| 约束 | 说明 |
|------|------|
| **租户** | `https://REDACTED-SAP-TENANT.example.com`，client `100` |
| **认证** | Basic Auth（用户 `REDACTED_SAP_COMM_USER`），请求头 `Authorization: Basic <base64>` |
| **必带参数** | `sap-client=100`、`$format=json`、`Accept: application/json` |
| **采购订单** | **必须用 `api_purchaseorder_2`（带 `_2`，V4 SAP_COM_0053）**，旧路径 `api_purchaseorder`（无 `_2`）会 403。V2 `API_PURCHASEORDER_PROCESS_SRV` legacy 可用但字段较少 |
| **供应商发票** | **V2 可用（`API_SUPPLIERINVOICE_PROCESS_SRV`，推荐）**，V4（SAP_COM_0054）全部 403 需开通 Arrangement |
| **主数据 SAP_COM_0087** | **全部 403**（付款条件/工厂/采购组织/采购组/公司代码/库存地点），需开通 Scope Item 1YB，**过渡期用替代方案**（见下文） |
| **OData 版本** | V2 路径 `/sap/opu/odata/sap/`；V4 路径 `/sap/opu/odata4/sap/.../srvd_a2x/sap/<name>/<ver>/` |

### 主数据 SAP_COM_0087 全 403 的替代方案（实测可用）

| 需求 | 替代 API（已 OK） | 通信场景 |
|------|-------------------|---------|
| 供应商名称 | `A_Supplier` | SAP_COM_0008 |
| 公司/公司代码名称 | `A_SupplierCompany.CompanyCodeName` | SAP_COM_0008 |
| 物料组描述 | `ProductGroup.ProductGroupName`（`api_productgroup_2`） | SAP_COM_0009 |
| 采购订单抬头备注 | `PurchaseOrderNote` | SAP_COM_0053 |

---

## 一、入站同步（ERP → 平台）

| 场景 | 关联 US | SAP 实测接口（通信场景 / 状态） | 方向 | 平台目标实体 | 平台既有 API（参考） |
|------|---------|-------------------------------|------|-------------|-------------------|
| INT-01 采购预测 | US-301 | ⚠️ `API_PLANNED_ORDERS` 未在 33 端点中探测；替代：采购申请 `API_PURCHASEREQ`（SAP_COM_0102，**未探测**） | 入站 | PurchaseForecast | `POST /collaboration/forecasts`、`POST /collaboration/forecasts/{id}/publish`、`GET /collaboration/forecasts` |
| INT-02 采购订单 | US-303 | ✅ V4 `api_purchaseorder_2`（SAP_COM_0053，7 entity 全 OK）：PurchaseOrder / PurchaseOrderItem / PurchaseOrderScheduleLine / PurOrderItemPricingElement / PurchaseOrderNote / PurchaseOrderItemNote / POSubcontractingComponent；✅ V2 `API_PURCHASEORDER_PROCESS_SRV/A_PurchaseOrder`（legacy OK） | 入站 | PurchaseOrder + OrderLineItem | `POST /purchase-orders/`、`GET /purchase-orders/`、`GET /purchase-orders/{id}` |
| INT-04 订单变更 | US-304 | ✅ 同 INT-02（`api_purchaseorder_2` 读取变更版本） | 入站 | PurchaseOrder | `PUT /purchase-orders/{id}`、`DELETE /purchase-orders/{id}` |
| INT-05 要货计划 | US-305 | ⚠️ 计划协议 `API_PURCHASING_SCHEDULE_AGREEMENT_SRV`（SAP_COM_0103，**未探测**，手册 5.3 标注） | 入站 | DeliverySchedule | `POST /collaboration/delivery-schedules`、`GET /collaboration/delivery-schedules` |
| INT-07 收货单 | US-310 | ✅ `API_MATERIAL_DOCUMENT_SRV/A_MaterialDocumentHeader`（SAP_COM_0108，OK） | 入站 | Receipt | `POST /logistics/receipts/`、`GET /logistics/receipts/`、`GET /logistics/receipts/{id}` |
| INT-08 质检结果 | US-310 | ⚠️ `API_INSPECTIONLOT_SRV` 未在 33 端点中探测，**待验证** | 入站 | QualityInspection | `POST /inspections/`（核实是否内嵌于 logistics） |
| INT-09 已收货未结算明细 | US-401 | ✅ 替代方案：`API_SUPPLIERINVOICE_PROCESS_SRV/A_SuplrInvcItemPurOrdRef`（V2 OK）按 PO 关联查询 | 入站 | 结算可选明细 | `GET /financial/statements/`（供应商创建结算单时引用） |
| INT-12 付款状态 | US-405 | ⚠️ `API_JOURNALENTRY_SRV` 未在 33 端点中探测，**待验证**；过渡期可从供应商发票付款状态推断 | 入站 | Payment | `POST /financial/payments/`、`GET /financial/payments/`、`GET /financial/payments/{id}` |
| INT-13 供应商主数据 | US-108 | ✅ `A_Supplier` + `A_SupplierCompany`（SAP_COM_0008，均 OK） | 入站 | Supplier (sap_vendor_code) | `GET /suppliers/`、`PUT /suppliers/{id}` |
| INT-14 预测基础数据 | US-302 | 随 INT-01 同步 | 入站 | 预测维度数据 | `GET /collaboration/forecasts/{id}/responses`、`POST /collaboration/forecasts/{id}/responses` |
| INT-15 物料主数据 | 通用 | ✅ V2 `API_PRODUCT_SRV/A_Product`（SAP_COM_0009，OK）；✅ V4 `api_product/.../Product`（OK）；✅ 物料组 `api_productgroup_2`（OK） | 入站 | Material (sap_material_code) | `GET /materials/`、`POST /materials/`、`PUT /materials/{id}` |

### INT-10 财务主数据（特殊处理）

| 需求 | 原计划接口 | 实测状态 | 替代方案（已 OK） |
|------|-----------|---------|------------------|
| 公司代码 | `api_companycode`（SAP_COM_0087） | ❌ 403 | `A_SupplierCompany.CompanyCodeName`（SAP_COM_0008） |
| 付款条件 | `api_paymentterms`（SAP_COM_0087） | ❌ 403 | 从采购订单 `PurchaseOrder.PaymentTerms`（SAP_COM_0053）读取 |
| 工厂 | `api_plant`（SAP_COM_0087） | ❌ 403 | 从采购订单行 `PurchaseOrderItem.Plant` 读取 |
| 采购组织 | `api_purchasingorganization`（SAP_COM_0087） | ❌ 403 | 从采购订单 `PurchaseOrder.PurchasingOrganization` 读取 |

---

## 二、出站回传（平台 → ERP）

出站场景由**平台既有业务路由的事件钩子**触发，集成层监听这些事件后调用 SAP RFC/OData 回传。

| 场景 | 关联 US | 触发事件（平台 API） | SAP 回传接口 | 实测状态 | 幂等键 |
|------|---------|---------------------|-------------|---------|--------|
| INT-03 订单确认/拒绝/异议 | US-303 | `POST /purchase-orders/{id}/supplier-confirm`<br>`POST /purchase-orders/{id}/supplier-reject`<br>`POST /purchase-orders/{id}/supplier-objection`<br>（供应商端：`POST /supplier-portal/orders/{id}/confirm`） | RFC `BAPI_PO_CHANGE`（ME22N） | ⚠️ RFC 未在 OData 探测范围，需单独验证 | 平台订单号 + 操作类型 |
| INT-06 要货计划确认/调整 | US-306 | `POST /collaboration/delivery-schedules/{id}/supplier-confirm`<br>`POST /supplier-portal/delivery-schedules/{id}/confirm` | OData `API_PURCHASING_SCHEDULE_AGREEMENT_SRV` UPDATE | ⚠️ 计划协议读取未探测，UPDATE 需验证 | 计划协议号 + 行项目 + 操作类型 |
| INT-11 发票校验 MIRO | US-403 | `POST /financial/invoices/{id}/approve` | RFC `BAPI_INCOMINGINVOICE_CREATE`（MIRO） | ⚠️ RFC 需单独验证；**读取侧** `API_SUPPLIERINVOICE_PROCESS_SRV`（V2 OK）可验证发票 | 发票号（不可重复过账） |

> **RFC 出站说明**：33 端点探测仅覆盖 OData READ。RFC/BAPI（`BAPI_PO_CHANGE`、`BAPI_INCOMINGINVOICE_CREATE`）需通过 SAP RFC 协议单独连通性验证。Demo 阶段用 MockSAPServer 模拟，真实联调时需 SAP Basis 团队配合开通。

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

## 四、SAP 侧实测端点完整清单（33 个）

### 4.1 ✅ 可用端点（24 个 OK）

#### SAP 上游（14 个全 OK）

| 接口名称 | 通信场景 | 协议 | Entity / 路径 |
|----------|---------|------|--------------|
| 产品主数据 V2 | SAP_COM_0009 | OData V2 | `API_PRODUCT_SRV/A_Product` |
| 客户主数据 V2 | SAP_COM_0008 | OData V2 | `API_BUSINESS_PARTNER/A_Customer` |
| 销售订单 V4 | SAP_COM_0109 | OData V4 | `api_salesorder/.../SalesOrder` |
| 生产订单 V4 | SAP_COM_0104 | OData V4 | `api_productionorder/.../ProductionOrder` |
| 外向交货 V2 | SAP_COM_0106 | OData V2 | `API_OUTBOUND_DELIVERY_SRV;v=0002/A_OutbDeliveryHeader` |
| 开票 V2 | SAP_COM_0124 | OData V2 | `API_BILLING_DOCUMENT_SRV/A_BillingDocument` |
| 物料库存 V2 | SAP_COM_0164 | OData V2 | `API_MATERIAL_STOCK_SRV/A_MatlStkInAcctMod` |
| 采购订单 V2 | legacy | OData V2 | `API_PURCHASEORDER_PROCESS_SRV/A_PurchaseOrder` |
| 产品主数据 V4 | SAP_COM_0009 | OData V4 | `api_product/.../Product` |
| 物料组 V4 | SAP_COM_0009 | OData V4 | `api_productgroup_2/.../ProductGroup` |
| 供应商 V2 | SAP_COM_0008 | OData V2 | `API_BUSINESS_PARTNER/A_Supplier` |
| 供应商公司 V2 | SAP_COM_0008 | OData V2 | `API_BUSINESS_PARTNER/A_SupplierCompany` |
| 物料凭证 V2 | SAP_COM_0108 | OData V2 | `API_MATERIAL_DOCUMENT_SRV/A_MaterialDocumentHeader` |
| 成本中心 V4 | SAP_COM_0008 | OData V4 | `api_cost_center/.../A_CostCenter_2` |

#### EPC 采购（7 个全 OK，SAP_COM_0053，V4）

服务根：`/sap/opu/odata4/sap/api_purchaseorder_2/srvd_a2x/sap/purchaseorder/0001/`

| Entity Set | 用途 |
|------------|------|
| `PurchaseOrder` | 采购订单抬头 |
| `PurchaseOrderItem` | 行项目 |
| `PurchaseOrderScheduleLine` | 计划行（交货日期） |
| `PurOrderItemPricingElement` | 行定价（税） |
| `PurchaseOrderNote` | 抬头备注 |
| `PurchaseOrderItemNote` | 行备注 |
| `POSubcontractingComponent` | 委外组件 |

#### EPC 应付 V2（3 个 OK，推荐使用）

服务：`API_SUPPLIERINVOICE_PROCESS_SRV`

| 操作 | URL 模式 |
|------|----------|
| 列表 | `.../A_SupplierInvoice?$top=50&$format=json&sap-client=100` |
| 单张 | `.../A_SupplierInvoice(SupplierInvoice=''{Invoice}'',FiscalYear=''{Year}'')?$format=json&sap-client=100` |
| 行(PO参考) | `.../A_SuplrInvcItemPurOrdRef?$filter=SupplierInvoice eq ''{Invoice}'' and FiscalYear eq ''{Year}''&$format=json&sap-client=100` |

**已验证示例**：发票 `5105600101` / 年度 `2025`，行项目关联 PO `4500000000/10`，金额 12000 CNY。

### 4.2 ❌ 不可用端点（9 个 403）

#### EPC 应付 V4（3 个 403，需开通 SAP_COM_0054）

| Entity | 状态 |
|--------|------|
| `SupplierInvoice`（V4） | FAIL(403) |
| `SuplrInvcItemPurOrdRef`（V4） | FAIL(403) |
| `SupplierInvoiceTax`（V4） | FAIL(403) |

#### 主数据 SAP_COM_0087（6 个全 403，需开通 Scope Item 1YB）

| 接口名称 | Entity | API 服务 |
|----------|--------|----------|
| 付款条件 V4 | `PaymentTerms` | `api_paymentterms` |
| 工厂 V4 | `Plant` | `api_plant` |
| 采购组织 V4 | `A_PurchasingOrganization` | `api_purchasingorganization` |
| 采购组 V4 | `A_PurchasingGroup` | `api_purchasinggroup` |
| 公司代码 V4 | `CompanyCode` | `api_companycode` |
| 库存地点 V4 | `StorageLocation` | `api_storagelocation` |

### 4.3 ⚠️ 未探测端点（URS 需要但不在 33 端点中）

| 场景 | 接口 | 通信场景 | 状态 | 建议 |
|------|------|---------|------|------|
| INT-01 采购预测 | `API_PLANNED_ORDERS` | — | 未探测 | 探测或改用采购申请 `API_PURCHASEREQ`（SAP_COM_0102） |
| INT-05 要货计划 | `API_PURCHASING_SCHEDULE_AGREEMENT_SRV` | SAP_COM_0103 | 未探测 | 手册 5.3 已标注，需探测 |
| INT-08 质检结果 | `API_INSPECTIONLOT_SRV` | — | 未探测 | 需探测，或从物料凭证推断 |
| INT-12 付款状态 | `API_JOURNALENTRY_SRV` | — | 未探测 | 需探测，过渡期从发票付款状态推断 |
| INT-03/11 出站 RFC | `BAPI_PO_CHANGE` / `BAPI_INCOMINGINVOICE_CREATE` | — | RFC 未探测 | 需 SAP Basis 配合单独验证 |

---

## 五、字段映射（INT-02 采购订单，对齐 URS 12.3）

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

> **V4 字段名差异**：V4 `api_purchaseorder_2` 用的是 `PurchaseOrder`（非 `A_PurchaseOrder`），字段名为 camelCase（如 `PurchaseOrder`、`Supplier`、`CompanyCode`、`PurchasingOrganization`、`PaymentTerms`），实现时需在 `field_mappings` 表配置 V2/V4 双映射。

---

## 六、对实现计划的影响（修订要点）

基于实测数据，对 `docs/superpowers/plans/2026-07-06-sap-s4hana-integration.md` 的修订：

1. **INT-02 采购订单**：MockSAPServer 必须模拟 `api_purchaseorder_2`（V4，7 entity），不是 URS 写的 `API_PURCHASE_ORDER_PROCESS_SRV`。字段映射需支持 V4 camelCase。
2. **INT-09 结算明细**：改用 `A_SuplrInvcItemPurOrdRef`（V2 OK）按 PO 关联查询，而非 URS 的 `I_PurchaseOrderHistory`。
3. **INT-10 财务主数据**：SAP_COM_0087 全 403，**过渡期用替代方案**（从采购订单/供应商公司读取），不阻塞 Phase 3。
4. **INT-13 供应商主数据**：用 `A_Supplier` + `A_SupplierCompany`（V2 OK），非 URS 的 `API_BUSINESS_PARTNER_SRV`。
5. **INT-01/05/08/12**：4 个场景的 SAP 接口未实测，MockSAPServer 按理论接口实现并标注 `待验证`，真实联调前需补充探测。
6. **MockSAPServer 配置**：base_url、client、认证方式须与真实租户一致（`REDACTED-SAP-TENANT.example.com` / client 100 / Basic Auth），便于后续切换。
7. **ODataConnector**：须同时支持 V2（`/sap/opu/odata/sap/`）和 V4（`/sap/opu/odata4/sap/.../srvd_a2x/`）两种路径模式。