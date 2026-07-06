# SAP S/4HANA 集成层 Implementation Plan（Ralph-loop TODO）— V2 实测驱动版

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 基于 `docs/URS-SAP-S4HANA-Integration.md` 与实测连通性数据，实现平台与 SAP S/4HANA Public Cloud 的双向集成层，覆盖 15 个集成场景（INT-01~INT-15）与 6 个管理需求（INT-M01~INT-M06）。

**Architecture:** 在现有 FastAPI 后端中新增 `app/integration/` 模块，采用「连接器 + 适配器 + 消息总线」三层架构。**优先接通实测可用的 7 个真实 SAP 接口**（INT-01/02/07/09/13/15），3 个 403 场景（INT-05/08/12）用 MockSAPServer 过渡，开通 Arrangement 后切换配置即可对接真实 SAP。

**Tech Stack:** Python 3.12 / FastAPI 0.109 / SQLAlchemy 2.0 (async) / aiosqlite / APScheduler / httpx（OData 异步 HTTP）/ pytest

## Global Constraints

- **部署模型：SAP S/4HANA Public Cloud（公有云）**，集成协议为 OData V2/V4 over HTTPS，**不适用 RFC/BAPI**。出站写操作用 OData PATCH/POST，经 Communication Arrangement（SAP_COM_xxxx）授权。
- **实测可用接口（7 个，2026-07-06 验证）**：INT-01 `API_PLANNED_ORDERS`、INT-02 `api_purchaseorder_2`（V4）/ `API_PURCHASEORDER_PROCESS_SRV`（V2）、INT-07 `API_MATERIAL_DOCUMENT_SRV`、INT-09 `API_SUPPLIERINVOICE_PROCESS_SRV`、INT-13 `API_BUSINESS_PARTNER`、INT-15 `API_PRODUCT_SRV`。
- **实测 403 接口（3 个，需开通 Arrangement）**：INT-05 `API_PURCHASING_SCHEDULE_AGREEMENT_SRV`（SAP_COM_0103）、INT-08 `API_INSPECTIONLOT_SRV`、INT-12 `API_JOURNALENTRY_SRV`。用 MockSAPServer 实现，开通后切换。
- **真实租户**：`https://REDACTED-SAP-TENANT.example.com`，client `100`，用户 `REDACTED_SAP_COMM_USER`，Basic Auth，必带 `sap-client=100`、`$format=json`、`Accept: application/json`。凭证从 `Integration/user.txt` 读取（gitignore）。
- **采购订单必须用 `api_purchaseorder_2`**（带 `_2`，V4 SAP_COM_0053），旧路径 403。
- **供应商发票用 V2**（`API_SUPPLIERINVOICE_PROCESS_SRV`），V4（SAP_COM_0054）403。
- **幂等键**：入站 = `SAP 单据号 + 行项目号 + 最后变更时间戳`；出站 = `平台单据号 + 操作类型`。
- **重试策略**：间隔 `30s → 2min → 10min → 30min`，最多 4 次。
- **不改业务逻辑**：集成层只替换数据来源，`app/api/` 与 `app/services/` 既有业务路由与领域服务签名不变；现有 67 条 US 烟测必须持续通过。
- **数据库**：沿用 SQLite（aiosqlite），新增集成相关表与 `app/core/database.Base` 共享同一 engine。
- **测试纪律**：TDD；集成测试用真实 SAP（可用场景）+ Mock（403 场景）；用例串行执行，不并行。

---

## 实测状态矩阵（驱动 Phase 划分）

| 场景 | SAP 接口 | 实测 | 开发方式 | Phase |
|------|---------|------|---------|-------|
| INT-01 采购预测 | API_PLANNED_ORDERS | ✅ 200 | 真实接口 | Phase 1 |
| INT-02 采购订单 | api_purchaseorder_2 (V4) | ✅ 200 | 真实接口 | Phase 1 |
| INT-07 收货单 | API_MATERIAL_DOCUMENT_SRV | ✅ 200 | 真实接口 | Phase 1 |
| INT-09 结算明细 | API_SUPPLIERINVOICE_PROCESS_SRV | ✅ 200 | 真实接口 | Phase 1 |
| INT-13 供应商主数据 | API_BUSINESS_PARTNER | ✅ 200 | 真实接口 | Phase 1 |
| INT-15 物料主数据 | API_PRODUCT_SRV | ✅ 200 | 真实接口 | Phase 1 |
| INT-04 订单变更 | 同 INT-02 | ✅ 200 | 真实接口 | Phase 1 |
| INT-05 要货计划 | API_PURCHASING_SCHEDULE_AGREEMENT_SRV | ❌ 403 | Mock 过渡 | Phase 2 |
| INT-08 质检结果 | API_INSPECTIONLOT_SRV | ❌ 403 | Mock 过渡 | Phase 2 |
| INT-12 付款状态 | API_JOURNALENTRY_SRV | ❌ 403 | Mock 过渡 | Phase 2 |
| INT-14 预测基础数据 | 随 INT-01 | ✅ 200 | 真实接口 | Phase 1 |
| INT-03 订单确认回传 | OData PATCH | ✅ 读OK,写待验证 | 真实接口+写验证 | Phase 3 |
| INT-06 要货确认回传 | OData UPDATE | ❌ 403 | Mock 过渡 | Phase 3 |
| INT-11 发票校验回传 | OData POST | ✅ 读OK,写待验证 | 真实接口+写验证 | Phase 3 |
| INT-10 财务主数据 | SAP_COM_0087 全403 | ❌ 403 | 替代方案 | Phase 2 |

---

# Phase 0：最小基础设施（仅支撑真实接口接通）

> 目标：搭最小骨架，让 Phase 1 能立即接通真实 SAP 接口。不搞大而全。

## Task 0.1：集成层模型与配置

**关联需求**：INT-M01-01, INT-M04-01, INT-M05-01, INT-M06-01/02

**验收条件**：
- [ ] 新增 `app/integration/models.py`，定义 5 张表：`sync_logs`、`sync_queue`、`field_mappings`、`scenario_configs`、`idempotency_records`
- [ ] `app/config.py` 新增 SAP 配置项（基于 `Integration/README.md` 第 1 节）：`SAP_BASE_URL`、`SAP_CLIENT`、`SAP_COMM_USER`、`SAP_COMM_PASSWORD`（从 user.txt 读）、`SAP_CREDENTIALS_FILE`
- [ ] `init_db.py` 执行后自动建表并填充默认场景配置（15 个 INT 场景，enabled 按实测状态设置：7 个 true，3 个 403 的 false）
- [ ] 测试：`test_models.py` 验证建表成功、默认场景配置数量与 enabled 状态正确

---

## Task 0.2：OData 连接器（真实 SAP，非 Mock）

**关联需求**：URS 3.3 原则 2

**验收条件**：
- [ ] 新增 `connector/base.py`，定义 `BaseConnector`：`async connect()`、`async health_check()`、`async read(scenario, params)`、`async write(scenario, payload)`
- [ ] 新增 `connector/odata_connector.py`，用 httpx 实现 OData V2/V4 读取，**直接对接真实租户** `REDACTED-SAP-TENANT.example.com`
- [ ] 支持从 `Integration/user.txt` 解析凭证（支持 `password：` 全角冒号格式）
- [ ] 支持 V2（`/sap/opu/odata/sap/`）和 V4（`/sap/opu/odata4/sap/.../srvd_a2x/`）双路径
- [ ] health_check 调用真实 SAP（如 `API_PRODUCT_SRV`），返回连通状态
- [ ] 测试：`test_odata_connector.py` 真实连接 SAP，验证 7 个可用端点返回 200（标记 `@pytest.mark.sap`，需凭证）

**实现要点**：
- 请求头：`Authorization: Basic <base64>`、`Accept: application/json`、`sap-client: 100`
- 查询参数：`$format=json&sap-client=100`
- 超时 25s，异常时写 `sync_logs`

---

## Task 0.3：适配器基类与同步编排（真实优先）

**关联需求**：INT-M06-03, INT-M02-01

**验收条件**：
- [ ] 新增 `adapter/base.py`，定义 `BaseAdapter`：`sap_to_platform(raw_sap_data) -> dict`、`platform_to_sap(platform_data) -> dict`
- [ ] 新增 `service/sync_service.py`，实现同步编排：`async run_inbound(scenario_code)` = 拉取 → 映射 → 幂等校验 → 持久化 → 写日志
- [ ] 幂等逻辑：以 `SAP 单据号 + 行项目号 + 最后变更时间戳` 为键查 `idempotency_records`
- [ ] 失败时写入 `sync_queue`，按 `30s → 2min → 10min → 30min` 重试
- [ ] 测试：`test_sync_service.py` 验证正常同步、重复同步幂等跳过、失败入队重试
- [ ] **阶段回归**：原有 67 条 US 烟测仍全部通过

---

# Phase 1：接通真实可用接口（7 个场景，核心交付）

> 目标：把实测可用的 7 个场景全部接通真实 SAP，跑通端到端数据流。

## Task 1.1：INT-02 采购订单同步（真实接口）

**关联 US/需求**：US-303, INT-02

**验收条件**：
- [ ] 新增 `adapter/purchase_order_adapter.py`：V4 `api_purchaseorder_2/PurchaseOrder` + `PurchaseOrderItem` + `PurchaseOrderScheduleLine` → 平台 `PurchaseOrder` + `OrderLineItem`
- [ ] 字段映射对齐 `Integration/README.md` 第 6.1 节（EBELN→sap_po_number 等），支持 V4 camelCase
- [ ] 同步后状态"待供应商确认"，通知供应商（对接现有 US-303 通知逻辑）
- [ ] 同一 SAP 订单号重复同步幂等更新；行删除标记"已删除"不物理删除
- [ ] 测试：`test_scenarios/test_int_02.py` **真实连接 SAP**，验证同步、幂等、行删除（`@pytest.mark.sap`）

---

## Task 1.2：INT-13 供应商主数据 + INT-15 物料主数据同步（真实接口）

**关联 US/需求**：US-108, INT-13；通用, INT-15

**验收条件**：
- [ ] 新增 `adapter/master_data_adapter.py`：`A_Supplier` + `A_SupplierCompany`（SAP_COM_0008）→ 平台 Supplier；`API_PRODUCT_SRV/A_Product`（SAP_COM_0009）→ 平台 Material
- [ ] 供应商：同步 sap_vendor_code、公司代码等字段；物料：同步 sap_material_code
- [ ] 每日定时拉取
- [ ] 测试：`test_scenarios/test_int_13_15.py` **真实连接 SAP**，验证主数据同步（`@pytest.mark.sap`）

---

## Task 1.3：INT-07 收货单 + INT-09 结算明细同步（真实接口）

**关联 US/需求**：US-310, INT-07；US-401, INT-09

**验收条件**：
- [ ] 新增 `adapter/goods_receipt_adapter.py`：`API_MATERIAL_DOCUMENT_SRV/A_MaterialDocumentHeader`（SAP_COM_0108）→ 平台 Receipt
- [ ] INT-09：复用 `API_SUPPLIERINVOICE_PROCESS_SRV/A_SuplrInvcItemPurOrdRef`（V2 OK）按 PO 关联查询已收货未结算明细
- [ ] 收货单同步后供应商可查看（对接 US-310-2）；结算明细供供应商创建结算单引用
- [ ] 测试：`test_scenarios/test_int_07_09.py` **真实连接 SAP**（`@pytest.mark.sap`）

---

## Task 1.4：INT-01 采购预测 + INT-14 基础数据同步（真实接口）

**关联 US/需求**：US-301, INT-01；US-302, INT-14

**验收条件**：
- [ ] 新增 `adapter/forecast_adapter.py`：`API_PLANNED_ORDERS/A_PlannedOrder`（实测 ✅ 200）→ 平台 PurchaseForecast
- [ ] INT-14 随 INT-01 同步预测基础数据（采购组、供应商分配维度）
- [ ] 同步后触发供应商通知（对接 US-302 协同流程）
- [ ] 测试：`test_scenarios/test_int_01_14.py` **真实连接 SAP**（`@pytest.mark.sap`）
- [ ] **阶段回归**：Phase 1 全部场景测试通过 + 原有 67 条 US 烟测通过

---

# Phase 2：Mock 过渡场景（3 个 403 + INT-10 替代方案）

> 目标：3 个 403 场景用 MockSAPServer 实现，接口签名与真实一致，开通 Arrangement 后切换配置即可。INT-10 用替代方案。

## Task 2.1：MockSAPServer 框架（仅用于 403 场景）

**验收需求**：支撑 INT-05/08/12

**验收条件**：
- [ ] 新增 `connector/mock_sap.py`，仅模拟 3 个 403 场景的数据源：INT-05 计划协议、INT-08 检验批、INT-12 日记账
- [ ] Mock 数据字段与 URS 附录、SAP 标准 CDS View 一致（`A_SchedgAgrmt`、`A_InspectionLot`、`A_JournalEntry`）
- [ ] 通过 `scenario_configs.enabled=false` + `use_mock=true` 配置切换真实/Mock
- [ ] 测试：`test_mock_sap.py` 验证 3 个场景 Mock 数据可读、字段完整

---

## Task 2.2：INT-05 要货计划同步（Mock 过渡）

**关联 US/需求**：US-305, INT-05

**验收条件**：
- [ ] 新增 `adapter/delivery_schedule_adapter.py`：`A_SchedgAgrmt` → 平台 DeliverySchedule
- [ ] 数据源：MockSAPServer（真实接口 403，开通 SAP_COM_0103 后切换）
- [ ] 同步后供应商可查看要货计划（对接 US-305）
- [ ] 测试：`test_scenarios/test_int_05.py` 用 Mock 验证同步与查看
- [ ] **切换验证**：开通 Arrangement 后改 `use_mock=false`，真实接口应直接可用

---

## Task 2.3：INT-08 质检结果 + INT-12 付款状态同步（Mock 过渡）

**关联 US/需求**：US-310, INT-08；US-405, INT-12

**验收条件**：
- [ ] 新增 `adapter/inspection_adapter.py`：`A_InspectionLot` → 平台 QualityInspection（Mock 数据源）
- [ ] 新增 `adapter/payment_adapter.py`：`A_JournalEntry` → 平台 Payment 状态（Mock 数据源）
- [ ] 质检结果与收货单关联；付款状态同步后供应商可查看（对接 US-405-2）
- [ ] 测试：`test_scenarios/test_int_08_12.py` 用 Mock 验证
- [ ] **阶段回归**：Phase 2 场景测试通过 + 原有 67 条 US 烟测通过

---

## Task 2.4：INT-10 财务主数据（替代方案，非 Mock）

**关联 US/需求**：US-403, INT-10

**验收条件**：
- [ ] SAP_COM_0087 全 403，用替代方案：从 `A_SupplierCompany.CompanyCodeName`（SAP_COM_0008 ✅）取公司代码；从 `PurchaseOrder.PaymentTerms/PurchasingOrganization`（SAP_COM_0053 ✅）取付款条件/采购组织
- [ ] 不新建独立同步，作为 INT-13/INT-02 适配器的附加字段
- [ ] 测试：`test_scenarios/test_int_10.py` 验证替代方案取数正确（`@pytest.mark.sap`）

---

# Phase 3：出站回传（真实写验证 + Mock 过渡）

> 目标：出站写操作，能用真实的验证写权限，403 的用 Mock。

## Task 3.1：INT-03 订单确认回传（真实接口 + 写权限验证）

**关联 US/需求**：US-303, INT-03

**验收条件**：
- [ ] 新增 `adapter/outbound_adapters.py` 中 `PurchaseOrderConfirmOutbound`：OData V4 **PATCH** `api_purchaseorder_2/PurchaseOrder`（SAP_COM_0053）
- [ ] 平台事件触发：供应商确认/拒绝/异议时回传
- [ ] **写权限验证**：发送测试 PATCH，确认 201/204（成功）或 403（需开通 UPDATE）
- [ ] 回传失败入队重试 3 次；幂等键 = `平台订单号 + 操作类型`
- [ ] 测试：`test_scenarios/test_int_03.py`（`@pytest.mark.sap`，写权限 403 时降级为 Mock 验证逻辑）

---

## Task 3.2：INT-11 发票校验回传（真实接口 + 写权限验证）

**关联 US/需求**：US-403, INT-11

**验收条件**：
- [ ] `outbound_adapters.py` 中 `InvoiceVerificationOutbound`：OData V2 **POST** `API_SUPPLIERINVOICE_PROCESS_SRV/A_SupplierInvoice`（等价 MIRO）
- [ ] 平台发票审批通过后触发；SAP 返回发票校验凭证号
- [ ] **写权限验证**：发送测试 POST，确认 201 或 403
- [ ] 同一发票号不可重复过账（幂等）
- [ ] 测试：`test_scenarios/test_int_11.py`（`@pytest.mark.sap`）

---

## Task 3.3：INT-06 要货确认回传（Mock 过渡）

**关联 US/需求**：US-306, INT-06

**验收条件**：
- [ ] `outbound_adapters.py` 中 `DeliveryScheduleConfirmOutbound`：OData UPDATE（INT-05 读 403，写也 403，用 Mock）
- [ ] 确认 → 计划行标记"供应商已确认"；调整建议 → 写入备注
- [ ] 测试：`test_scenarios/test_int_06.py` 用 Mock 验证
- [ ] **阶段回归**：Phase 3 场景测试通过 + 原有 67 条 US 烟测通过

---

# Phase 4：集成管理功能

## Task 4.1：INT-M01 同步日志 + INT-M02 重试补偿 + INT-M06 幂等去重

**验收条件**：
- [ ] 每条同步写 `sync_logs`，含 URS INT-M01-01 全部字段；日志保留 ≥ 90 天
- [ ] `GET /integration/logs` 支持按场景/单据号/时间/状态检索、排序、导出
- [ ] `service/retry_service.py` 消费 `sync_queue`，按 `30s→2min→10min→30min` 重试最多 4 次
- [ ] `POST /integration/retry/{log_id}` 手动重推；`POST /integration/retry/batch` 批量重推
- [ ] 幂等键校验完整覆盖入站/出站
- [ ] 测试：`test_sync_log.py`、`test_retry_service.py`

---

## Task 4.2：INT-M03 监控告警 + INT-M04 字段映射 + INT-M05 场景开关

**验收条件**：
- [ ] `service/monitor_service.py` 概览看板：各场景最近同步时间/成功率/积压数
- [ ] ERP 心跳探针每 60s 一次（调用真实 SAP health_check），断连告警
- [ ] `service/config_service.py` 字段映射 CRUD 与热加载；场景独立启停
- [ ] 暂停期间数据入队，恢复后自动补传
- [ ] 测试：`test_monitor_service.py`、`test_config_service.py`
- [ ] **阶段回归**：Phase 4 全部管理功能测试通过 + 原有 67 条 US 烟测通过

---

# Phase 5：管理前端界面

## Task 5.1：集成管理前端

**验收条件**：
- [ ] `frontend/src/pages/admin/SyncLogList.tsx`：日志列表，筛选/排序/导出
- [ ] `frontend/src/pages/admin/MonitorDashboard.tsx`：场景同步概览 + ERP 连接状态 + 告警
- [ ] `frontend/src/pages/admin/FieldMappingConfig.tsx`：字段映射配置
- [ ] `frontend/src/pages/admin/ScenarioControl.tsx`：场景开关、手动重推、批量重推
- [ ] `App.tsx` + `Layout.tsx` 新增管理员菜单与路由；`api/index.ts` 新增集成管理 API
- [ ] 前端构建通过：`cd frontend && pnpm build`

---

# Phase 6：全量回归验收

## Task 6.1：全量回归与 URS 验收

**验收条件**：
- [ ] 集成层全部场景测试通过：`pytest backend/tests/integration/ -v`
- [ ] 原有 67 条 US 烟测仍全部通过：`pytest tests/api/test_user_stories_smoke.py -v`
- [ ] URS 第 11 节场景验收逐条核对
- [ ] URS 第 11.2 节非功能验收：断线恢复、重复推送幂等、日志检索、监控告警、场景开关
- [ ] 更新 `docs/RALPH-TODO.md` 勾选集成层闭环
- [ ] 更新 `README.md` 集成层状态
- [ ] **最终 review**：派 final code-reviewer 做整分支审查