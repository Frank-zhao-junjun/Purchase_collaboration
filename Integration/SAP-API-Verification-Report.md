# SAP S/4HANA API 核对报告

| 项目 | 值 |
|------|-----|
| 文档版本 | V2.0 |
| 核对日期 | 2026-07-06 |
| **目标系统** | **SAP S/4HANA Cloud Public Edition** |
| 核对范围 | URS-SAP-S4HANA-Integration V0.2 附录 12.1 / 12.2 全部 12 个接口 |
| 数据来源 | SAP API Business Hub (api.sap.com)、SAP KBA (support.sap.com)、SAP Build Process Automation 模板 |
| 关联文档 | `docs/URS-SAP-S4HANA-Integration.md` |

---

## 1. 核对结果总览

| 类别 | 总数 | ✅ 已确认 | ⚠️ 已废弃 | ❌ 未找到 |
|------|------|----------|-----------|----------|
| OData 服务 | 10 | 7 | 3 | 0 |
| RFC/BAPI | 2 | 2 | 0 | 0 |
| **合计** | **12** | **9** | **3** | **0** |

**关键发现**：
- INT-02 / INT-04 / INT-09 使用的 `API_PURCHASEORDER_PROCESS_SRV` 已被 SAP 标注废弃，需迁移至 v4 替代 `API_PURCHASE_ORDER_2`
- 其余 9 个 OData 接口全部确认为活跃且可用
- **INT-03 和 INT-11 的 BAPI 在 S/4HANA Public Cloud 中不可用于外部系统集成**，必须替换为 OData/SOAP API（详见第 6 节）
- **新增**：INT-03 需使用 Supplier Confirmation OData V4 API 和 `API_PURCHASEORDER_2` PATCH 替代 `BAPI_PO_CHANGE`
- **新增**：INT-11 需使用 `API_SUPPLIERINVOICE_PROCESS_SRV` (OData v2) 替代 `BAPI_INCOMINGINVOICE_CREATE`

---

## 2. OData 服务核对明细

### 2.1 INT-01 — 计划订单读取

| 项 | 值 |
|----|-----|
| OData 服务名 | `API_PLANNED_ORDERS` |
| CDS View | `I_PlannedOrder` |
| OData 版本 | v2 |
| 服务路径 | `/sap/opu/odata/sap/API_PLANNED_ORDERS` |
| 实体集 | `A_PlannedOrder` |
| 核对状态 | ✅ 已确认 |
| 验证来源 | SAP API Business Hub sandbox 端点活跃 |

### 2.2 INT-02 — 采购订单读取 ⚠️

| 项 | 值 |
|----|-----|
| 原服务名 | `API_PURCHASEORDER_PROCESS_SRV` |
| 原版本 | v2 |
| **核对状态** | **⚠️ 已废弃** |
| SAP 标注 | "now deprecated" |
| **v4 替代** | `API_PURCHASE_ORDER_2` |
| v4 服务路径 | `/sap/opu/odata4/sap/api_purchaseorder_2/srvd_a2x/sap/purchaseorder/0001/` |
| 通信场景 | `SAP_COM_0053` |
| 验证来源 | SAP API Business Hub — Purchase Order (v2) 页面显示 deprecated 横幅 |

**迁移影响**：
- 实体名变化：`PurchaseOrder` → `A_PurchaseOrder`（v4 命名规范）
- 导航路径变化：v4 中 PO → PO Item 的 `$expand` 语法有差异
- 查询参数：v4 不支持 v2 的 `$format=json`（默认 JSON），`$filter` 函数名有部分变化（如 `substringof` → `contains`）

### 2.3 INT-04 — 采购订单变更版本读取 ⚠️

| 项 | 值 |
|----|-----|
| 原服务名 | `API_PURCHASEORDER_PROCESS_SRV` |
| 原版本 | v2 |
| **核对状态** | **⚠️ 已废弃** |
| 迁移方案 | 同 INT-02，迁移至 `API_PURCHASE_ORDER_2` (v4) |
| 通信场景 | `SAP_COM_0053` |

### 2.4 INT-05 — 采购计划协议读取

| 项 | 值 |
|----|-----|
| OData 服务名 | `API_PURCHASING_SCHEDULE_AGREEMENT_SRV` |
| CDS View | `I_PurchasingSchedgAgrmt` |
| OData 版本 | v2 |
| 服务路径 | `/sap/opu/odata/sap/API_PURCHASING_SCHEDULE_AGREEMENT_SRV` |
| 核对状态 | ✅ 已确认 |
| 验证来源 | SAP KBA 3708479（2026-01）确认 RAP 业务对象 `i_schedgagrmthdrtp_2` 活跃 |

### 2.5 INT-07 — 物料凭证读取

| 项 | 值 |
|----|-----|
| OData 服务名 | `API_MATERIAL_DOCUMENT_SRV` |
| CDS View | `I_MaterialDocument` |
| OData 版本 | v2 |
| 服务路径 | `/sap/opu/odata/sap/API_MATERIAL_DOCUMENT_SRV` |
| 通信场景 | `SAP_COM_0108` |
| 核对状态 | ✅ 已确认 |
| 验证来源 | SAP Build Process Automation "Automate Posting of Goods Receipt" 模板中活跃使用 |

### 2.6 INT-08 — 检验批读取

| 项 | 值 |
|----|-----|
| OData 服务名 | `API_INSPECTIONLOT_SRV` |
| CDS View | `I_InspectionLot` |
| OData 版本 | v2 |
| 服务路径 | `/sap/opu/odata/sap/API_INSPECTIONLOT_SRV` |
| 适用版本 | SAP S/4HANA 2022+ |
| 范围项 | 1FM（采购质量管理） |
| 核对状态 | ✅ 已确认 |

### 2.7 INT-09 — 采购订单历史读取 ⚠️

| 项 | 值 |
|----|-----|
| 原服务名 | `API_PURCHASEORDER_PROCESS_SRV` |
| 原实体 | `I_PurchaseOrderHistory` |
| 原版本 | v2 |
| **核对状态** | **⚠️ 已废弃** |
| 迁移方案 | 迁移至 `API_PURCHASE_ORDER_2` (v4)，PO History 通过导航属性 `$expand=A_PurchaseOrderHistory` 访问 |
| 通信场景 | `SAP_COM_0053` |

### 2.8 INT-12 — 日记账凭证读取

| 项 | 值 |
|----|-----|
| OData 服务名 | `API_JOURNALENTRY_SRV` |
| CDS View | `I_JournalEntry` |
| OData 版本 | v2 |
| 服务路径 | `/sap/opu/odata/sap/API_JOURNALENTRY_SRV` |
| 核对状态 | ✅ 已确认 |
| 注意事项 | OData API 仅支持**读取**日记账行项目。如需**创建**日记账过账，应使用 SOAP API `JournalEntryBulkCreateRequest`（sfin 命名空间），而非 OData |

### 2.9 INT-13 — 业务伙伴读取

| 项 | 值 |
|----|-----|
| OData 服务名 | `API_BUSINESS_PARTNER`（无 `_SRV` 后缀） |
| CDS View | `I_BusinessPartner` |
| OData 版本 | v2 |
| 服务路径 | `/sap/opu/odata/sap/API_BUSINESS_PARTNER` |
| 实体集 | `A_BusinessPartner` |
| 通信场景 | `SAP_COM_0008` |
| 核对状态 | ✅ 已确认 |

### 2.10 INT-15 — 物料主数据读取

| 项 | 值 |
|----|-----|
| OData 服务名 | `API_PRODUCT_SRV` |
| CDS View | `I_Product` |
| OData 版本 | v2 |
| 服务路径 | `/sap/opu/odata/sap/API_PRODUCT_SRV` |
| 通信场景 | `SAP_COM_0009` |
| 核对状态 | ✅ 已确认 |
| 验证来源 | SAP Build Process Automation "Product Master Data Management" 模板中活跃使用 |

---

## 3. RFC/BAPI 核对明细 — ⚠️ Public Cloud 不适用

> **关键约束**：S/4HANA Cloud Public Edition 不允许外部非 SAP 系统通过 RFC/BAPI 集成。以下两个 BAPI 需替换为 OData API（见第 6 节）。此处保留核对信息仅作参考。

### 3.1 INT-03 — 采购订单确认更新

| 项 | 值 |
|----|-----|
| 函数模块 | `BAPI_PO_CHANGE` |
| 事务码 | `ME22N` |
| 操作 | UPDATE（确认字段） |
| 核对状态 | ✅ BAPI 仍活跃（On-Premise） |
| **Public Cloud 可用性** | **❌ 不可用** — 需替换为 OData API |
| 已知限制 | SC vendor 更新、确认创建等部分字段有限制；SAP KBA 1775915 指出无法通过 BAPI 创建确认，仅可更新 |
| **替代方案** | Supplier Confirmation OData V4 API（CDS `I_POSupplierConfirmationAPI01`，SAP KBA 3401990）+ `API_PURCHASEORDER_2` PATCH |

### 3.2 INT-11 — 发票校验创建

| 项 | 值 |
|----|-----|
| 函数模块 | `BAPI_INCOMINGINVOICE_CREATE` |
| 事务码 | `MIRO` |
| 操作 | CREATE（发票校验） |
| 核对状态 | ✅ BAPI 仍活跃（On-Premise） |
| **Public Cloud 可用性** | **❌ 不可用** — 需替换为 OData API |
| 已知限制 | 替代统账科目、Bill of Lading、Earmarked Funds 字段不可用 |
| **替代方案** | `API_SUPPLIERINVOICE_PROCESS_SRV` (OData v2)，通信场景 `SAP_COM_0057` |

> **注意**：SAP KBA 3377659 确认 `API_SUPPLIERINVOICE_PROCESS_SRV` 内部实际上是调用 `BAPI_INCOMINGINVOICE_CREATE`，但作为 SAP 官方发布的 Cloud API，它是 Public Cloud 环境下的合规集成路径。

---

## 4. 通信场景映射汇总

实现集成时需在 SAP S/4HANA Cloud Public Edition 中通过 Fiori 应用 "Communications Arrangements" 配置以下通信场景：

| 通信场景 | 用途 | 涉及场景 |
|---------|------|---------|
| `SAP_COM_0053` | 采购订单 | INT-02, INT-04, INT-09 |
| `SAP_COM_0057` | 供应商发票 | **INT-11（替代 BAPI）** |
| `SAP_COM_0008` | 业务伙伴 | INT-13 |
| `SAP_COM_0009` | 物料主数据 | INT-15 |
| `SAP_COM_0108` | 物料凭证 | INT-07 |
| — (待确认) | 计划订单 | INT-01 |
| — (待确认) | 采购计划协议 | INT-05 |
| — (待确认) | 检验批 | INT-08 |
| — (待确认) | 日记账凭证 | INT-12 |
| — (待确认) | 供应商确认（PO Confirmation） | INT-03 |

> 标注"待确认"的场景需在实现阶段通过 SAP `I_ServiceName` 或 `I_CommunicationScenario` 视图查询对应通信场景。

---

## 5. v2 → v4 迁移指南（INT-02 / INT-04 / INT-09）

### 5.1 背景

SAP 正在将 API 从 OData v2 迁移至 v4。当前受影响的是采购订单 API：

```
v2 (废弃):  API_PURCHASEORDER_PROCESS_SRV
            路径: /sap/opu/odata/sap/API_PURCHASEORDER_PROCESS_SRV

v4 (当前):   API_PURCHASE_ORDER_2
            路径: /sap/opu/odata4/sap/api_purchaseorder_2/srvd_a2x/sap/purchaseorder/0001/
```

### 5.2 关键差异

| 方面 | v2 | v4 |
|------|----|----|
| URL 路径前缀 | `/sap/opu/odata/sap/` | `/sap/opu/odata4/sap/` |
| 实体集命名 | `PurchaseOrder` | `A_PurchaseOrder` |
| 响应格式 | XML/JSON（`$format` 参数） | JSON（默认，不支持 `$format`） |
| `$filter` 字符串函数 | `substringof('x', Field)` | `contains(Field, 'x')` |
| `$filter` 逻辑运算 | `eq`, `and`, `or` | `eq`, `and`, `or`（相同） |
| 分页 | `$inlinecount=allpages` | `@$count` 路径后缀 |
| `$expand` 语法 | `?$expand=Items` | `?$expand=A_PurchaseOrderItem` |
| 错误格式 | v2 error XML/JSON | v4 OData error JSON |

### 5.3 迁移步骤

1. **更新通信场景配置**：确认 `SAP_COM_0053` 已在 SAP 系统中激活
2. **更新基类 URL**：从 v2 路径切换到 v4 路径
3. **更新实体名映射**：在 OData 客户端配置中将 v2 实体名映射到 v4
4. **更新 `$filter` 表达式**：替换 `substringof` → `contains`，移除 `$format=json`
5. **更新分页逻辑**：将 `$inlinecount` 替换为 `/$count` 独立请求
6. **测试错误处理**：验证 v4 错误响应解析
7. **回归测试**：对 INT-02/04/09 三个场景进行端到端测试

---

## 6. S/4HANA Public Cloud — BAPI 替代方案

### 6.1 架构约束

S/4HANA Cloud Public Edition 的集成架构与 On-Premise 有本质区别：

| 方面 | On-Premise | Public Cloud |
|------|-----------|-------------|
| 可用接口 | OData + BAPI/RFC + IDoc + 直接表访问 | **仅 OData + SOAP**（SAP 发布的公开 API） |
| 自定义开发 | 可自定义 ABAP 开发 | ❌ 不允许修改核心 |
| 直接表访问 | ✅ 允许 | ❌ 禁止 |
| 认证方式 | Basic Auth / SAML / X.509 | **OAuth 2.0**（推荐）或 Basic Auth（通过 Communication Arrangement） |
| 通信配置 | 通过 SOAMANAGER / SICF | 通过 Fiori 应用 "Communication Arrangements" |

**SAP Note 2447593 核心约束**：RFC/BAPI 仅推荐用于 S/4HANA Cloud 与 SAP On-Premise 系统之间的集成。非 SAP 系统通过 RFC/BAPI 集成 S/4HANA Cloud 属于"风险自负"范畴，且在 Public Cloud 中技术上不可行（无 RFC 监听端点暴露给外部）。

### 6.2 INT-03 替代方案 — 采购订单确认更新

`BAPI_PO_CHANGE` 在 Public Cloud 中不可用。需拆分为两个场景：

#### 6.2.1 采购订单字段更新

| 项 | 值 |
|----|-----|
| API | `API_PURCHASE_ORDER_2` (OData v4) |
| 操作 | `PATCH /sap/opu/odata4/sap/api_purchaseorder_2/srvd_a2x/sap/purchaseorder/0001/PurchaseOrder('{PurchaseOrder}')` |
| 通信场景 | `SAP_COM_0053` |
| 支持的 PO 类型 | 仅标准类型 "NB" 及从 "NB" 复制的自定义类型（SAP KBA 3555741, 3669206） |
| 已知限制 | 不可更新序列号（SAP KBA 3498768）；自定义 PO 类型可能报 "Operation is not enabled" |

#### 6.2.2 供应商确认创建/更新

| 项 | 值 |
|----|-----|
| API | **Supplier Confirmation OData V4** |
| CDS View | `I_POSupplierConfirmationAPI01` |
| 操作 | POST（创建）、PATCH（更新）、DELETE（删除） |
| 来源 | SAP KBA 3401990 — "Supplier Confirmation API For Purchase Order" |
| 已知限制 | 不支持批量处理（每次操作一条确认） |
| SOAP 替代 | `OrderConfirmationRequest_In`（范围项 2EJ） |

### 6.3 INT-11 替代方案 — 发票校验创建

`BAPI_INCOMINGINVOICE_CREATE` 在 Public Cloud 中不可用。

| 项 | 值 |
|----|-----|
| **OData API** | `API_SUPPLIERINVOICE_PROCESS_SRV` (OData v2) |
| 服务路径 | `/sap/opu/odata/sap/API_SUPPLIERINVOICE_PROCESS_SRV` |
| 实体集 | `A_SupplierInvoice` |
| 操作 | POST（创建）、GET（读取）、POST `/Release`（释放）、POST `/Reverse`（冲销） |
| 通信场景 | `SAP_COM_0057` |
| **SOAP 替代** | `ECC_SUPLRINVCERPCRTRC`（`SupplierInvoiceERPCreateRequestConfirmation_In`） |
| 支持的发票类型 | PO 参考发票、GR 参考发票、服务确认参考发票、GL 账户行发票、物料行发票、一次性供应商发票 |
| 已知限制 | Profit Center 和 Functional Area 不会自动推导（需在 payload 中显式提供，SAP KBA 3377659）；替代统账科目字段需通过 SSCUI 102631 配置（SAP KBA 3761861） |

#### 示例请求（创建供应商发票）：

```http
POST /sap/opu/odata/sap/API_SUPPLIERINVOICE_PROCESS_SRV/A_SupplierInvoice
Content-Type: application/json

{
  "CompanyCode": "1000",
  "DocumentDate": "/Date(1782336000000)/",
  "PostingDate": "/Date(1782336000000)/",
  "SupplierInvoiceIDByFiscalYear": "2026",
  "InvoicingParty": "0010000001",
  "DocumentCurrency": "CNY",
  "InvoiceGrossAmount": "10000.00",
  "SupplierInvoiceItem": [
    {
      "PurchaseOrder": "4500000001",
      "PurchaseOrderItem": "10",
      "QuantityInPurchaseOrderUnit": "100",
      "PurchaseOrderQuantityUnit": "EA",
      "SupplierInvoiceItemAmount": "10000.00",
      "TaxCode": "V1"
    }
  ]
}
```

### 6.4 认证与授权配置

在 S/4HANA Cloud Public Edition 中，所有 API 调用都需要通过 Communication Arrangement 进行认证配置：

1. 在 Fiori 应用 **"Communication Systems"** 中创建通信系统（指定外部系统的主机名、用户）
2. 在 Fiori 应用 **"Communication Arrangements"** 中为每个通信场景（如 `SAP_COM_0053`、`SAP_COM_0057`）创建安排
3. 获取 OAuth 2.0 客户端凭证（client_id / client_secret）
4. 调用 API 时先通过 `https://{host}/oauth/token` 获取 access_token，再以 `Bearer` token 调用 OData API

---

## 7. 后续行动项

| 优先级 | 行动项 | 关联场景 | 负责方 |
|--------|--------|---------|--------|
| **P0** | **将 INT-03 从 `BAPI_PO_CHANGE` 替换为 Supplier Confirmation OData V4 + `API_PURCHASEORDER_2` PATCH** | **INT-03** | 架构组 + 集成开发 |
| **P0** | **将 INT-11 从 `BAPI_INCOMINGINVOICE_CREATE` 替换为 `API_SUPPLIERINVOICE_PROCESS_SRV`** | **INT-11** | 架构组 + 集成开发 |
| P0 | 将 INT-02/04/09 的 API 引用从 v2 切换到 v4 `API_PURCHASE_ORDER_2` | INT-02, 04, 09 | 集成开发 |
| P0 | 更新 URS 附录 12.3 字段映射，适配 v4 实体命名 | INT-02 | 需求分析 |
| P1 | 确认 INT-01/03/05/08/12 对应的 SAP 通信场景 | INT-01, 03, 05, 08, 12 | SAP Basis |
| P1 | 更新 URS 附录 12.2 RFC/BAPI 清单为 OData/SOAP API 清单 | INT-03, 11 | 需求分析 |
| P1 | 确认 PO 类型是否为 "NB"（`API_PURCHASEORDER_2` PATCH 仅支持 NB 及派生类型） | INT-03 | 业务分析 |
| P2 | INT-12 如需创建日记账，补充 SOAP API 集成方案设计 | INT-12 | 集成开发 |
| P2 | 配置 Communication Arrangements（OAuth 2.0 认证） | 全部 | SAP Basis |

---

## 变更记录

| 日期 | 版本 | 变更内容 | 变更人 |
|------|------|---------|--------|
| 2026-07-06 | V1.0 | 初稿创建，包含 12 个接口核对结果、v2→v4 迁移指南、部署环境注意事项 | Agent |
| 2026-07-06 | V2.0 | 标注目标系统为 S/4HANA Public Cloud；INT-03/11 BAPI 替换为 OData API；新增通信场景 SAP_COM_0057；添加 OAuth 2.0 认证配置说明；添加 Supplier Confirmation OData V4 API | Agent |
