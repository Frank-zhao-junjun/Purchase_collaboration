# SAP S/4HANA 集成层 Implementation Plan（Ralph-loop TODO）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 基于 `docs/URS-SAP-S4HANA-Integration.md`，实现平台与 SAP S/4HANA ERP 的双向集成层，覆盖 15 个集成场景（INT-01~INT-15）与 6 个管理需求（INT-M01~INT-M06），替换当前 `init_db.py` 的种子数据模拟。

**Architecture:** 在现有 FastAPI 后端中新增 `app/integration/` 模块，采用「连接器 + 适配器 + 消息总线」三层架构：连接器层封装 SAP OData/RFC 协议访问；适配器层负责 SAP 字段 ↔ 平台实体映射与转换；通过内部任务调度（APScheduler）驱动定时拉取，事件钩子驱动出站回传。集成层与业务层通过 `app/services/` 既有领域服务解耦，不修改业务逻辑，仅替换数据来源。

**Tech Stack:** Python 3.12 / FastAPI 0.109 / SQLAlchemy 2.0 (async) / aiosqlite / APScheduler（定时调度）/ httpx（OData 异步 HTTP）/ pyrfc 或 SAP REST API（RFC 出站，Demo 阶段以 mock 适配器替代）/ pytest

## Global Constraints

- **协议优先级**：入站优先 OData（`API_*_SRV` 服务），出站 RFC（`BAAPI_PO_CHANGE` / `BAPI_INCOMINGINVOICE_CREATE`）；Demo 阶段无真实 SAP 系统，所有外部协议访问通过 **mock 适配器** 实现，但接口签名与字段映射须与 URS 第 12 节附录一致，便于后续替换为真实实现。
- **幂等键**：入站 = `SAP 单据号 + 行项目号 + 最后变更时间戳`；出站 = `平台单据号 + 操作类型`（INT-M06-01/02）。
- **重试策略**：间隔 `30s → 2min → 10min → 30min`，最多 4 次（INT-M02-01）。
- **日志保留**：≥ 90 天，含场景编号/方向/SAP 单据号/平台单据号/同步时间/状态/错误信息（INT-M01-01）。
- **同步延迟阈值**：入站 15min / 出站 5min 超阈值告警（INT-M03-02）；ERP 心跳探针每 60s 一次（INT-M03-03）。
- **平台不写回 ERP 业务数据**：出站仅回传「供应商协同结果」（确认/拒绝、ASN、结算单、发票审批）（URS 3.3 原则 1）。
- **不改业务逻辑**：集成层只替换数据来源，`app/api/` 与 `app/services/` 既有业务路由与领域服务签名不变；现有 67 条 US 烟测必须持续通过。
- **数据库**：沿用 SQLite（aiosqlite），新增集成相关表与 `app/core/database.Base` 共享同一 engine。
- **测试纪律**：每个 task 先写失败测试再实现（TDD）；集成测试用 mock 适配器，不依赖真实 SAP；用例串行执行（依赖共享状态 `ST`），不并行。

---

## 文件结构

```
backend/app/integration/               # 集成层根模块（新增）
├── __init__.py
├── models.py                          # 集成层 ORM 模型：SyncLog, SyncQueue, FieldMapping, ScenarioConfig, IdempotencyRecord
├── schemas.py                         # Pydantic schema：同步日志/队列/配置的请求响应模型
├── connector/
│   ├── __init__.py
│   ├── base.py                        # BaseConnector 抽象基类（connect/health_check/读/写）
│   ├── odata_connector.py             # ODataConnector：httpx 异步访问 S/4HANA OData 服务
│   ├── rfc_connector.py               # RFCConnector：BAPI 调用（Demo 用 mock）
│   └── mock_sap.py                    # MockSAPServer：模拟 ERP 数据源与回传应答（Demo 核心）
├── adapter/
│   ├── __init__.py
│   ├── base.py                        # BaseAdapter 抽象基类（sap_to_platform / platform_to_sap）
│   ├── forecast_adapter.py            # INT-01 计划订单 → PurchaseForecast
│   ├── purchase_order_adapter.py      # INT-02/04 EKKO/EKPO → PurchaseOrder + OrderLineItem
│   ├── delivery_schedule_adapter.py   # INT-05 计划协议 → DeliverySchedule
│   ├── goods_receipt_adapter.py       # INT-07 MIGO → Receipt
│   ├── inspection_adapter.py          # INT-08 QA11 → QualityInspection
│   ├── settlement_adapter.py          # INT-09 POHistory → 结算可选明细
│   ├── payment_adapter.py             # INT-12 F-53 → Payment 状态
│   ├── master_data_adapter.py         # INT-10/13/15 Vendor/CompanyCode/Material 主数据
│   └── outbound_adapters.py           # INT-03/06/11 出站回传适配器
├── service/
│   ├── __init__.py
│   ├── sync_service.py                # 同步编排：拉取→映射→持久化→日志，含幂等与重试
│   ├── retry_service.py               # 重试与补偿队列消费（INT-M02）
│   ├── monitor_service.py             # 监控/心跳/告警（INT-M03）
│   └── config_service.py              # 字段映射/场景开关热加载（INT-M04/M05）
├── scheduler.py                        # APScheduler 调度器：注册各场景定时任务
└── api.py                             # 集成管理路由：/integration/logs, /monitor, /config, /retry

backend/app/api/integration_admin.py   # 管理前端调用的 REST 路由（挂载到 main.py）
backend/tests/integration/             # 集成层测试（新增）
├── conftest.py                        # 共享 fixture：mock SAP、干净 DB、ST 状态
├── test_mock_sap.py                   # MockSAPServer 数据源测试
├── test_adapters/                     # 各适配器字段映射测试
├── test_sync_service.py               # 同步编排/幂等/重试测试
└── test_scenarios/                    # INT-01~INT-15 端到端场景测试

frontend/src/pages/admin/              # 集成管理前端（Phase 5）
├── SyncLogList.tsx
├── MonitorDashboard.tsx
├── FieldMappingConfig.tsx
└── ScenarioControl.tsx
```

---

## Ralph-loop 执行原则

1. **一次只做 1 条最小 task**（SDD：fresh implementer per task）。
2. **每条 task 必须有明确验收条件**（对应 URS 需求编号）。
3. **先补测试或对齐现有测试，再改实现**（TDD）。
4. **改完立刻跑最小验证**：`pytest backend/tests/integration/test_<scenario>.py -v`（串行，不并行）。
5. **每个 Phase 完成后跑阶段回归**；Phase 6 跑全量回归（含原有 67 条 US 烟测 + 集成层场景）。
6. **task review**：每条 task 完成后派 task-reviewer subagent 审 spec 合规 + 代码质量；Critical/Important 必须修复后重审。
7. **最终 review**：全部 task 完成后派 final code-reviewer 做整分支审查。

---

# Phase 0：集成层基础设施

## Task 0.1：集成层模型与数据库迁移

**关联需求**：INT-M01-01, INT-M04-01, INT-M05-01, INT-M06-01/02

**验收条件**：
- [ ] 新增 `app/integration/models.py`，定义 5 张表：`sync_logs`、`sync_queue`、`field_mappings`、`scenario_configs`、`idempotency_records`
- [ ] 表结构字段与 URS INT-M01-01 / INT-M04-01 / INT-M05-01 / INT-M06-01/02 完全对应
- [ ] 模型基于 `app.core.database.Base`，`init_db.py` 执行后自动建表并填充默认场景配置（15 个 INT 场景 + 6 个管理场景，默认 enabled=true）
- [ ] 测试：`test_models.py` 验证建表成功、默认场景配置数量正确

**实现要点**：
- `sync_logs`：id, scenario_code, direction(inbound/outbound), sap_doc_number, platform_doc_number, sync_time, status(success/fail/retrying), error_message, request_payload(Text), response_payload(Text)
- `scenario_configs`：id, scenario_code, enabled, sync_frequency, last_sync_time, priority
- `field_mappings`：id, scenario_code, sap_field, platform_field, transform_rule(JSON)
- `idempotency_records`：id, idempotency_key(unique), scenario_code, last_sync_time
- `sync_queue`：id, scenario_code, payload, status(pending/processing/done/failed), retry_count, next_retry_time

---

## Task 0.2：Mock SAP Server 与连接器基类

**关联需求**：URS 3.3 原则 2、第 12 节附录

**验收条件**：
- [ ] 新增 `connector/mock_sap.py`，模拟 S/4HANA 数据源：提供 15 个场景的预置测试数据（采购订单、计划订单、收货凭证等），数据字段与 URS 第 12.3 节字段映射示例一致
- [ ] 新增 `connector/base.py`，定义 `BaseConnector` 抽象基类：`async connect()`、`async health_check()`、`async read(scenario, params)`、`async write(scenario, payload)`
- [ ] 新增 `connector/odata_connector.py`，继承 `BaseConnector`，用 httpx 实现 OData 读取（Demo 阶段指向 MockSAPServer 的 HTTP 端点）
- [ ] 新增 `connector/rfc_connector.py`，继承 `BaseConnector`，实现 BAPI 调用签名（Demo 阶段委托 MockSAPServer）
- [ ] 测试：`test_mock_sap.py` 验证各场景数据可读、字段完整；连接器 health_check 返回连通状态

**实现要点**：
- MockSAPServer 以 FastAPI 子应用或独立 dict 形式提供，启动时加载 `mock_data/` 下的 JSON
- ODataConnector 的 URL/认证从 `config.py` 读取（`SAP_ODATA_BASE_URL`、`SAP_AUTH_TOKEN`），Demo 默认指向 mock
- 字段严格对齐 URS 12.3：EKKO-EBELN → sap_po_number 等

---

## Task 0.3：适配器基类与同步编排服务

**关联需求**：INT-M06-03, INT-M02-01

**验收条件**：
- [ ] 新增 `adapter/base.py`，定义 `BaseAdapter`：`sap_to_platform(raw_sap_data) -> dict`、`platform_to_sap(platform_data) -> dict`
- [ ] 新增 `service/sync_service.py`，实现同步编排：`async run_inbound(scenario_code)` = 拉取 → 映射 → 幂等校验 → 持久化 → 写日志
- [ ] 幂等逻辑：以 `SAP 单据号 + 行项目号 + 最后变更时间戳` 为键查 `idempotency_records`，命中且时间戳未变则跳过（INT-M06-01/03）
- [ ] 失败时写入 `sync_queue`，按 `30s → 2min → 10min → 30min` 计算下次重试（INT-M02-01）
- [ ] 测试：`test_sync_service.py` 验证正常同步、重复同步幂等跳过、失败入队重试

---

## Task 0.4：调度器与管理路由骨架

**关联需求**：INT-M03-01, INT-M05-01

**验收条件**：
- [ ] 新增 `scheduler.py`，用 APScheduler 注册定时任务：INT-01 每 4h、INT-02 每 15min、INT-05 每 1h 等（频率取自 URS 5.1 场景矩阵）
- [ ] 调度器随 FastAPI 启动（`main.py` lifespan），各场景是否调度受 `scenario_configs.enabled` 控制（INT-M05-01）
- [ ] 新增 `api/integration_admin.py`，提供骨架路由：`GET /integration/monitor/overview`（INT-M03-01）、`GET /integration/logs`、`POST /integration/retry/{log_id}`、`GET/PUT /integration/scenarios`、`GET/PUT /integration/field-mappings`
- [ ] 挂载到 `main.py`，不破坏现有路由
- [ ] 测试：调度器启动后各场景任务注册成功；管理路由可返回空数据不报错
- [ ] **阶段回归**：原有 67 条 US 烟测仍全部通过

---

# Phase 1：入站同步 P0 场景

## Task 1.1：INT-01 采购预测同步

**关联 US/需求**：US-301, INT-01

**验收条件**：
- [ ] 新增 `adapter/forecast_adapter.py`：SAP 计划订单（`API_PLANNED_ORDERS`）→ 平台 `PurchaseForecast` 实体
- [ ] MockSAPServer 提供计划订单测试数据（物料编号、工厂、计划数量、计划日期、采购组、供应商分配）
- [ ] 业务规则：同一物料+工厂+计划日期以 ERP 最新覆盖；ERP 删除的计划订单平台标记"已取消"不物理删除；同步后触发供应商通知
- [ ] 测试：`test_scenarios/test_int_01.py` 验证同步后平台出现预测数据、重复同步幂等、删除标记生效

---

## Task 1.2：INT-02 采购订单同步

**关联 US/需求**：US-303, INT-02

**验收条件**：
- [ ] 新增 `adapter/purchase_order_adapter.py`：EKKO/EKPO → `PurchaseOrder` + `OrderLineItem`，字段映射对齐 URS 12.3
- [ ] 新增订单同步后状态为"待供应商确认"，通知供应商（调用现有 US-303 通知逻辑）
- [ ] 同一 SAP 订单号重复同步执行幂等更新，仅更新变更字段；行项目删除标记"已删除"不物理删除
- [ ] 测试：`test_scenarios/test_int_02.py` 验证新增/重复同步/行删除三个分支

---

## Task 1.3：INT-04 采购订单变更/关闭同步

**关联 US/需求**：US-304, INT-04

**验收条件**：
- [ ] 复用 `purchase_order_adapter.py` 读取变更版本，识别变更字段/前值/后值/时间/人
- [ ] 数量变更且供应商已确认 → 标记"订单已变更，需重新确认"并通知供应商
- [ ] 价格变更 → 记录价格历史并通知；交货日期变更 → 更新并通知
- [ ] 订单关闭 → 平台状态置"已关闭"
- [ ] 测试：`test_scenarios/test_int_04.py` 覆盖数量/价格/交货日期/关闭四类变更

---

## Task 1.4：INT-05 要货计划同步

**关联 US/需求**：US-305, INT-05

**验收条件**：
- [ ] 新增 `adapter/delivery_schedule_adapter.py`：计划协议（`API_PURCHASING_SCHEDULE_AGREEMENT_SRV`）→ 平台 `DeliverySchedule`
- [ ] MockSAPServer 提供计划协议交货计划数据
- [ ] 同步后供应商可在平台查看要货计划（对接现有 US-305 查看逻辑）
- [ ] 测试：`test_scenarios/test_int_05.py` 验证同步与查看

---

## Task 1.5：INT-07 收货单同步

**关联 US/需求**：US-310, INT-07

**验收条件**：
- [ ] 新增 `adapter/goods_receipt_adapter.py`：MIGO 101 物料凭证（`API_MATERIAL_DOCUMENT_SRV`）→ 平台 `Receipt`
- [ ] 收货单同步后供应商可查看（对接现有 US-310-2）
- [ ] 幂等：同一物料凭证号不重复创建
- [ ] 测试：`test_scenarios/test_int_07.py`

---

## Task 1.6：INT-08 质检结果同步

**关联 US/需求**：US-310, INT-08

**验收条件**：
- [ ] 新增 `adapter/inspection_adapter.py`：QA11 检验批判定（`API_INSPECTIONLOT_SRV`）→ 平台 `QualityInspection`
- [ ] 质检结果与收货单关联，供应商可查看合格/不合格结果
- [ ] 测试：`test_scenarios/test_int_08.py`

---

## Task 1.7：INT-09 已收货未结算明细同步

**关联 US/需求**：US-401, INT-09

**验收条件**：
- [ ] 复用 `purchase_order_adapter.py` 读取 `I_PurchaseOrderHistory`，筛选已收货未结算明细
- [ ] 供应商创建结算单时可看到可选明细列表（对接现有 US-401-1）
- [ ] 测试：`test_scenarios/test_int_09.py`

---

## Task 1.8：INT-12 付款状态同步

**关联 US/需求**：US-405, INT-12

**验收条件**：
- [ ] 新增 `adapter/payment_adapter.py`：F-53 付款凭证（`API_JOURNALENTRY_SRV`）→ 平台发票付款状态
- [ ] 付款状态同步后供应商可查看付款记录（对接 US-405-2）
- [ ] 测试：`test_scenarios/test_int_12.py`
- [ ] **阶段回归**：Phase 1 全部场景测试通过 + 原有 67 条 US 烟测通过

---

# Phase 2：出站回传场景

## Task 2.1：INT-03 采购订单确认/拒绝结果回传

**关联 US/需求**：US-303, INT-03

**验收条件**：
- [ ] 新增 `adapter/outbound_adapters.py` 中 `PurchaseOrderConfirmOutbound`：平台确认/拒绝/异议 → SAP PO 确认字段（`BAPI_PO_CHANGE`）
- [ ] 平台事件触发：供应商确认/拒绝/异议时，通过现有 `purchase_orders` 路由的回调钩子触发回传
- [ ] 回传失败入队重试 3 次，仍失败告警人工介入
- [ ] 幂等键 = `平台订单号 + 操作类型`
- [ ] 测试：`test_scenarios/test_int_03.py` 覆盖确认/拒绝/异议/失败重试

---

## Task 2.2：INT-06 要货计划确认/调整建议回传

**关联 US/需求**：US-306, INT-06

**验收条件**：
- [ ] `outbound_adapters.py` 中 `DeliveryScheduleConfirmOutbound`：确认/调整建议 → SAP 计划协议（`API_PURCHASING_SCHEDULE_AGREEMENT_SRV` 更新）
- [ ] 确认 → SAP 计划行标记"供应商已确认"；调整建议 → 写入备注不修改数量
- [ ] 测试：`test_scenarios/test_int_06.py`

---

## Task 2.3：INT-11 发票校验回传（MIRO）

**关联 US/需求**：US-403, INT-11

**验收条件**：
- [ ] `outbound_adapters.py` 中 `InvoiceVerificationOutbound`：平台发票审批通过 → `BAPI_INCOMINGINVOICE_CREATE` 在 SAP 创建发票校验凭证
- [ ] 三单匹配结果随发票传入 SAP 作为 MIRO 参考
- [ ] SAP 返回发票校验凭证号，平台记录关联；失败标记"回传失败"附 SAP 错误消息
- [ ] 同一发票号不可重复过账（幂等）
- [ ] 测试：`test_scenarios/test_int_11.py` 覆盖成功/失败/重复过账
- [ ] **阶段回归**：Phase 2 场景测试通过 + 原有 67 条 US 烟测通过

---

# Phase 3：入站同步 P1 场景

## Task 3.1：INT-10 财务主数据同步

**关联需求**：INT-10（Vendor/Company Code）

**验收条件**：
- [ ] 新增 `adapter/master_data_adapter.py` 中财务主数据同步：公司代码、付款条件映射
- [ ] 每日定时拉取，供应商创建结算单/发票时引用
- [ ] 测试：`test_scenarios/test_int_10.py`

---

## Task 3.2：INT-13 供应商主数据同步

**关联 US/需求**：US-108, INT-13

**验收条件**：
- [ ] `master_data_adapter.py` 中供应商主数据同步：`API_BUSINESS_PARTNER_SRV` → 平台供应商 sap_vendor_code 等字段
- [ ] 平台注册供应商通过名称/税号与 ERP 供应商主数据手动匹配（提供匹配接口）
- [ ] 每日定时拉取
- [ ] 测试：`test_scenarios/test_int_13.py`

---

## Task 3.3：INT-14 采购预测基础数据 + INT-15 物料主数据同步

**关联需求**：INT-14, INT-15

**验收条件**：
- [ ] INT-14 随 INT-01 同步预测基础数据（采购组、供应商分配维度）
- [ ] INT-15 物料主数据：`API_PRODUCT_SRV` → 平台物料 sap_material_code 等，每日定时拉取
- [ ] 测试：`test_scenarios/test_int_14_15.py`
- [ ] **阶段回归**：Phase 3 场景测试通过 + 原有 67 条 US 烟测通过

---

# Phase 4：集成管理功能

## Task 4.1：INT-M01 同步日志与审计

**验收条件**：
- [ ] `sync_service.py` 每条同步写 `sync_logs`，含 URS INT-M01-01 全部字段
- [ ] 日志保留 ≥ 90 天（定时清理任务）
- [ ] `GET /integration/logs` 支持按场景/单据号/时间范围/状态检索、排序、导出（INT-M01-02/03）
- [ ] 失败记录完整请求/响应报文（脱敏）（INT-M01-04）
- [ ] 测试：`test_sync_log.py`

---

## Task 4.2：INT-M02 重试与补偿 + INT-M06 幂等去重

**验收条件**：
- [ ] `service/retry_service.py` 消费 `sync_queue`，按 `30s→2min→10min→30min` 重试最多 4 次（INT-M02-01）
- [ ] 全部失败标记"需人工介入"并告警（INT-M02-02）
- [ ] `POST /integration/retry/{log_id}` 手动重推；`POST /integration/retry/batch` 按场景批量重推（INT-M02-03/04）
- [ ] 幂等键校验完整覆盖入站/出站（INT-M06-01/02/03）
- [ ] 测试：`test_retry_service.py`

---

## Task 4.3：INT-M03 同步状态监控

**验收条件**：
- [ ] `service/monitor_service.py` 提供概览看板数据：各场景最近同步时间/成功率/积压数（INT-M03-01）
- [ ] 延迟超阈值告警（入站 15min / 出站 5min）（INT-M03-02）
- [ ] ERP 心跳探针每 60s 一次，断连告警（INT-M03-03）
- [ ] 告警通知渠道：系统消息（邮件 P1 预留接口）（INT-M03-04）
- [ ] 测试：`test_monitor_service.py`

---

## Task 4.4：INT-M04 字段映射配置 + INT-M05 场景开关

**验收条件**：
- [ ] `service/config_service.py` 提供字段映射 CRUD 与热加载（INT-M04-01/02/03）
- [ ] 简单值转换（状态码映射、单位转换）（INT-M04-02）
- [ ] `GET/PUT /integration/scenarios` 每场景独立启停（INT-M05-01）
- [ ] 暂停期间数据入队，恢复后自动补传（INT-M05-02）；全局暂停/恢复（INT-M05-03）
- [ ] 测试：`test_config_service.py`
- [ ] **阶段回归**：Phase 4 全部管理功能测试通过 + 原有 67 条 US 烟测通过

---

# Phase 5：管理前端界面

## Task 5.1：同步日志与监控看板页面

**验收条件**：
- [ ] 新增 `frontend/src/pages/admin/SyncLogList.tsx`：日志列表，支持场景/单据号/时间/状态筛选、排序、导出
- [ ] 新增 `frontend/src/pages/admin/MonitorDashboard.tsx`：各场景最近同步时间/成功率/积压数卡片 + ERP 连接状态 + 告警列表
- [ ] 新增 `frontend/src/pages/admin/FieldMappingConfig.tsx`：字段映射配置表，支持编辑与热加载
- [ ] 新增 `frontend/src/pages/admin/ScenarioControl.tsx`：场景开关、手动重推、批量重推
- [ ] `App.tsx` + `Layout.tsx` 新增管理员菜单与路由
- [ ] `api/index.ts` 新增集成管理 API 函数
- [ ] 前端构建通过：`cd frontend && pnpm build`

---

# Phase 6：全量回归验收

## Task 6.1：全量回归与 URS 验收

**验收条件**：
- [ ] 集成层全部场景测试通过：`pytest backend/tests/integration/ -v`
- [ ] 原有 67 条 US 烟测仍全部通过：`pytest tests/api/test_user_stories_smoke.py -v`
- [ ] URS 第 11 节场景验收逐条核对：INT-01~INT-12 每条验收标准有对应测试覆盖
- [ ] URS 第 11.2 节非功能验收：断线恢复、重复推送幂等、日志检索、监控告警、场景开关
- [ ] 更新 `docs/RALPH-TODO.md` 勾选集成层闭环
- [ ] 更新 `README.md` 集成层状态
- [ ] **最终 review**：派 final code-reviewer 做整分支审查，通过后用 `superpowers:finishing-a-development-branch` 收尾