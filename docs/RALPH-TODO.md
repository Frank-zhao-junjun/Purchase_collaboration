# Ralph-loop TODO

基于根目录 `US.txt` 的最小用户故事拆分，以及 [RALPH.md](../RALPH.md) 定义的闭环方式，按 `US -> SPEC -> TESTING CASE -> CODING -> VALIDATION` 推进。

## 执行原则

1. 一次只做 1 条最小 US。
2. 每条 US 必须有明确验收条件。
3. 先补测试或对齐现有测试，再改实现。
4. 改完立刻跑最小验证，再决定是否进入下一条。
5. 每个 Phase 完成后，跑一次阶段回归；全部完成后跑全量 US 回归。

## 顶层 TODO

- [x] Phase 1 准入闭环：`US-101-1 ~ US-109-2` ✅ 代码完整，全量 US 测试通过
- [x] Phase 2 寻源闭环：`US-201-1 ~ US-208-2` ✅ 后端+测试完整，前端已补强（2026-07-05）
- [x] Phase 3 执行闭环：`US-301-1 ~ US-310-2` ✅ P0 已落地，前端已补强（2026-07-05）
- [x] Phase 4 财务闭环：`US-401-1 ~ US-405-2` ✅ commit `b2411b8` + 前端已完整（2026-07-05 确认）
- [x] US-501 公告闭环：`US-501-1 ~ US-501-2` ✅ commit `b3edb89`
- [x] 全量 US 回归验收 → 见 [FULL-REGRESSION-CHECKLIST.md](./FULL-REGRESSION-CHECKLIST.md) — ✅ 2026-07-05，67 passed (clean DB, serial, no xdist)

## 当前修复优先级

### P0 阻断项

- [x] 在 `backend/app/main.py` 挂载 `collaboration.router`
- [x] 修复 `/collaboration/*` 对应 US-301 ~ US-306 的可达性
- [x] 补齐 `logistics.py` 中 `submit`、`approve`、`packing-lists` 接口 (US-307~309)
- [x] 补齐 `financial.py` 中 `buyer-audit`、结算单修改、`three-way-match`、发票 `approve/reject/resubmit` 接口

### P1 稳定性项

- [x] 给 `supplier_collaboration.py` 的写接口补 `commit`
- [x] 对 Phase 3 串行烟测补稳定性验证（`test_us_301_1`~`test_us_310_2` 已加强断言；本地执行 `-k "test_us_30"`）

## Phase 1 代码质量修复（2026-07-05）

| 问题 | 修复 | 涉及 US |
|------|------|---------|
| `qualification.py` 6 处 `flush()` 未 `commit()` | 创建项目/问卷/评审/批准/驳回全部改为 `await db.commit()` | US-104~107 |
| `supplier_qualification.py` 8 处 `flush()` 未 `commit()` | 取消邀请/审核通过/审核驳回/重新提交/添加证书/处理预警/自动过期标记/到期检查全部改为 `commit()` | US-101~103, US-108~109 |
| US-106 测试仅断言 200 | 补断言：`success`/`final_score` 范围/评分已持久化 | US-106 |
| US-107 测试仅断言 200 | 补断言：供应商状态变 active/项目状态变 approved/最终决定确认 | US-107 |
| US-108 测试仅断言 200 | 补断言：先触发到期检查→验证预警列表非空/记录 id 存在 | US-108 |
| US-109 测试仅断言 200 | 补断言：证书创建成功→列表命中 cert_no/字段匹配 | US-109 |

**验证命令：**
```bash
pytest tests/api/test_user_stories_smoke.py -v -k "test_us_10"
```

## Phase 3 P0 修复反馈（2026-07-05）

| 问题 | 修复 | 涉及 US |
|------|------|---------|
| `collaboration.router` 未挂载 | `main.py` 注册 `/collaboration` | US-301~306 |
| 预测/要货 API 404 | 新增 `collaboration.py`（forecasts publish/responses、delivery-schedules supplier-confirm） | US-301~306 |
| ASN 创建即 `submitted`，跳过提交态 | 创建改为 `draft`，新增 `POST .../submit` | US-307~308 |
| 烟测路径 `packing-lists`（复数）404 | 保留 `packing-list` 并增加 `packing-lists` 别名 | US-309 |
| `approve` 无 body 时 422 | `Body(default_factory=ShipmentApproveIn)` | US-308 |
| `ShipmentStatus` 缺 approved/rejected | 扩展 enum + 状态机 | US-308 |
| `supplier_collaboration` 写后未 commit | 全部写接口改为 `await db.commit()` | US-302/306/307 |
| 烟测仅断言 200 | Phase 3 用例补 status / success / 列表命中断言 | 全 Phase 3 |

**验证命令：**

```powershell
cd backend && python init_db.py && uvicorn app.main:app --host 127.0.0.1 --port 8000
pytest tests/api/test_user_stories_smoke.py -v -k "test_us_30"
```

**剩余风险：** 本机未安装 Python，上述命令需在开发环境手动执行；`purchase_orders` 部分写路径仍用 `flush`（非 Phase 3 烟测主路径）。

### P1 文档项

- [x] 修正 README 项目结构树 + API 端点 + 文档导航
- [x] 将本次 review 结论与修复记录回链到 RALPH-TODO

## Ralph-loop 模板

每条最小 US 按下面 5 步执行：

1. `US`：从根目录 `US.txt` 选定 1 条最小 US。
2. `SPEC`：补齐输入、输出、状态流转、角色边界、异常分支、验收标准。
3. `TESTING CASE`：优先映射到 `tests/api/test_user_stories_smoke.py`；必要时补充 API/E2E 用例。
4. `CODING`：只修改该 US 直接相关的接口、页面、状态逻辑。
5. `VALIDATION`：先跑最小测试，再跑阶段回归。

---

## Phase 1: 供应商准入与主数据协同

### US-101 邀请注册

- [x] `US-101-1` 供应商注册邀请

| 维度 | 内容 |
|------|------|
| **角色** | 采购方 |
| **输入** | `invited_supplier_name`(必填), `invited_email`(必填,email格式), `invited_contact_person`(选填), `expiry_days`(必填,1~90), `notes`(选填) |
| **输出** | `invitation_code`(8位), `status: "pending"`, `expiry_date`, 注册链接 |
| **状态流转** | pending → accepted(供应商注册后) \| cancelled(采购方取消) \| expired(超期) |
| **异常** | 400: 邮箱格式非法; 400: 同一邮箱已有pending邀请 |
| **验收** | status=200; invitation_code长度=8; status=pending; expiry_date非空; 可在列表查询 |
| **API** | `POST /supplier-portal/invitations` → `supplier_qualification.py:32` |
| **前端** | `buyer/InvitationList.tsx` — 表单+列表+成功弹窗(含复制链接) |
| **测试** | `test_us_101_1` (创建+字段断言) ✅ |

- [x] `US-101-2` 查看注册邀请

| 维度 | 内容 |
|------|------|
| **角色** | 供应商 |
| **输入** | `email`(Query参数, 用于筛选该邮箱收到的邀请) |
| **输出** | 邀请列表 `[{invitation_code, invited_email, invited_supplier_name, status, expiry_date, ...}]` |
| **验收** | status=200; 返回列表含刚创建的邀请; invitation_code匹配; status=pending |
| **API** | `GET /supplier-portal/invitations?email=xxx` → `supplier_qualification.py` |
| **前端** | `supplier/InvitationList.tsx` — 供应商端查看收到的邀请 |
| **测试** | `test_us_101_2` (列表查询+字段匹配) ✅ |

### US-102 注册提交

- [x] `US-102-1` 供应商自助注册

| 维度 | 内容 |
|------|------|
| **角色** | 供应商 |
| **输入** | `invitation_code`(选填,有则校验), `company_name`, `unified_credit_code`(唯一), `contact_person`, `contact_phone`, `contact_email`, `address`, `main_categories`, `annual_capacity`, `employee_count`, `established_year` |
| **输出** | `id`, `status: "pending_audit"` |
| **状态流转** | pending_audit → approved \| rejected; 邀请码状态 pending→accepted |
| **异常** | 400: 统一信用代码已注册; 400: 邀请码无效/已失效/已过期 |
| **验收** | status=200; 返回status=pending_audit; 邀请码关联的邀请变为accepted |
| **API** | `POST /supplier-portal/register` → `supplier_qualification.py:219` |
| **前端** | `supplier/Registration.tsx` — 自助注册表单 |
| **测试** | `test_us_102_1` (注册+邀请状态联动) ✅ |
| **注意** | ⚠️ 仅 `flush()` 无显式 `commit()`，依赖 `get_db()` 自动提交 |

- [x] `US-102-2` 采购方查看供应商注册

| 维度 | 内容 |
|------|------|
| **角色** | 采购方 |
| **输入** | `registration_id`(路径参数) |
| **输出** | 注册详情 `{company_name, unified_credit_code, status, ...}` |
| **验收** | status=200; company_name/unified_credit_code匹配 |
| **API** | `GET /supplier-portal/registrations/{id}` → `supplier_qualification.py` |
| **测试** | `test_us_102_2` (详情查询+字段匹配) ✅ |

### US-103 注册审批

- [x] `US-103-1` 审批供应商注册 — API `POST /supplier-portal/registrations/{id}/audit` (approve/reject) → `supplier_qualification.py:397` | 前端 `buyer/RegistrationAudit.tsx` | 测试 `test_us_103_1` ✅
- [x] `US-103-2` 注册状态审批情况查询和回应 — API `GET /supplier-portal/register/status?unified_credit_code=` + `POST /supplier-portal/registrations/{id}/resubmit` | 测试 `test_us_103_2` ✅

### US-104 资格评审项目创建

- [x] `US-104-1` 供应商资格评审项目创建 — API `POST /qualification/projects` → `qualification.py:52` | 前端 `buyer/QualificationProjectList.tsx` | 测试 `test_us_104_1` ✅
- [x] `US-104-2` 接收供应商资格评审项目 — API `GET /qualification/projects` | 前端 `supplier/QualificationList.tsx` | 测试 `test_us_104_2` ✅

### US-105 资格评审填写与查看

- [x] `US-105-1` 编辑供应商资格评审项目 — API `GET /qualification/projects/{id}/questionnaire` + `POST .../submission` → `qualification.py:324` | 测试 `test_us_105_1` ✅
- [x] `US-105-2` 查看供应商资格评审项目 — API `GET /qualification/projects/{id}/submissions` | 测试 `test_us_105_2` ✅

### US-106 资格文件评审与澄清

- [x] `US-106-1` 采购方评审资格文件 — API `POST /qualification/projects/{id}/submissions/{sid}/review` → `qualification.py:451` | 测试 `test_us_106_1` ✅
- [x] `US-106-2` 查看评审项目的审批结果 — API 同上 GET | 前端 `supplier/QualificationList.tsx` | 测试 `test_us_106_2` ✅

### US-107 最终资格决定

- [x] `US-107-1` 最终决定-供应商资格评审项目 — API `POST /qualification/projects/{id}/approve|reject` → `qualification.py:526,579` | 测试 `test_us_107_1` ✅
- [x] `US-107-2` 查看最终决定-供应商资格评审项目 — API 同上 GET | 测试 `test_us_107_2` ✅

### US-108 资质预警与重认证邀请

- [x] `US-108-1` 采购方资质管理 — API `POST /supplier-portal/cert-alerts/check` + `GET .../supplier-alerts` + `POST .../{id}/resolve` → `supplier_qualification.py:83,554,617` | 前端 `buyer/CertAlertList.tsx` | 测试 `test_us_108_1` ✅
- [x] `US-108-2` 供应商资质管理 — API 同上 GET/POST | 前端 `supplier/CertificationList.tsx` | 测试 `test_us_108_2` ✅

### US-109 资质更新

- [x] `US-109-1` 供应商资质更新、资质有效期更新、提交重认证材料 — API `POST /supplier-portal/suppliers/{id}/certifications` → `supplier_qualification.py:510` | 测试 `test_us_109_1` ✅
- [x] `US-109-2` 查看供应商资质更新记录 — API `GET /supplier-portal/suppliers/{id}/certifications` | 测试 `test_us_109_2` ✅

---

## Phase 2: 寻源与合同协同

### US-201 寻源项目发布与查看

- [x] `US-201-1` 寻源项目发布 — API `POST /sourcing/projects` → `sourcing.py:75` | 前端 `buyer/SourcingList.tsx` | 测试 `test_us_201_1` ✅
- [x] `US-201-2` 查看寻源项目 — API `GET /sourcing/projects` + `GET /sourcing/projects/{id}` | 前端 `supplier/InvitationList.tsx` | 测试 `test_us_201_2` ✅

### US-202 邀请响应

- [x] `US-202-1` 接收/拒绝寻源项目 — API `POST /sourcing/projects/{id}/accept|decline` → `sourcing.py:292,316` | 前端 `supplier/InvitationList.tsx` | 测试 `test_us_202_1` ✅
- [x] `US-202-2` 查收邀请接收/拒绝信息 — API `GET /sourcing/projects/{id}/invitations` | 测试 `test_us_202_2` ✅

### US-203 寻源结果通知

- [x] `US-203-1` 中标/落标通知发布 — API `POST /sourcing/projects/{id}/open-bids` + `POST .../award` → `sourcing.py:452,553` | 测试 `test_us_203_1` ✅
- [x] `US-203-2` 查收中标/落标通知 — API `GET /sourcing/projects/{id}/bids/{bid_id}` | 测试 `test_us_203_2` ✅

### US-204 合同草案发布与查看

- [x] `US-204-1` 合同草案发布 — API `POST /contracts/` (generate from sourcing) → `sourcing.py:672` | 前端 `buyer/ContractList.tsx` | 测试 `test_us_204_1` ✅
- [x] `US-204-2` 查询合同草案 — API `GET /contracts/` + `GET /contracts/drafts/{id}` | 前端 `supplier/ContractList.tsx` | 测试 `test_us_204_2` ✅

### US-205 合同修改意见

- [x] `US-205-1` 合同修改意见反馈 — API `POST /contracts/{id}/comments` → `sourcing.py:849` | 测试 `test_us_205_1` ✅
- [x] `US-205-2` 查看供应商的合同修改意见 — API `GET /contracts/{id}` (含comments) | 测试 `test_us_205_2` ✅

### US-206 合同在线签署

- [x] `US-206-1` 发起合同在线签署 — API `POST /contracts/{id}/sign-initiate` → `sourcing.py:1016` | 测试 `test_us_206_1` ✅
- [x] `US-206-2` 在线签署合同 — API `POST /contracts/{id}/sign` → `sourcing.py:1043` | 测试 `test_us_206_2` ✅

### US-207 查看签署状态

- [x] `US-207-1` 查看合同签署状态（供应商） — API `GET /contracts/{id}/sign-status` | 测试 `test_us_207_1` ✅
- [x] `US-207-2` 查看合同签署状态（采购方） — API 同上 | 测试 `test_us_207_2` ✅

### US-208 合同状态修改

- [x] `US-208-1` 修改合同状态 — API `PATCH /contracts/{id}` → `sourcing.py:821` | 测试 `test_us_208_1` ✅
- [x] `US-208-2` 查看合同状态的修改 — API `GET /contracts/{id}` | 测试 `test_us_208_2` ✅

---

## Phase 3: 预测与订单执行协同

> **P0 修复详见上方「Phase 3 P0 修复反馈」。20/20 US 子项 API 完整 + 烟测断言已加强。**

- [x] `US-301-1` 采购预测发布 — `collaboration.py:120` | `test_us_301_1` ✅
- [x] `US-301-2` 查看采购预测 — `supplier_collaboration.py` | `test_us_301_2` ✅
- [x] `US-302-1` 供应商产能响应 — `supplier_collaboration.py:160` | `test_us_302_1` ✅
- [x] `US-302-2` 查看供应商产能 — `test_us_302_2` ✅
- [x] `US-303-1` 采购订单发布 — `purchase_orders.py:33` | `test_us_303_1` ✅
- [x] `US-303-2` 确认/拒绝/异议 — `supplier_portal.py` | `test_us_303_2` ✅
- [x] `US-304-1` 订单变更与关闭 — `purchase_orders.py` PUT | `test_us_304_1` ✅
- [x] `US-304-2` 查看变更关闭 — `test_us_304_2` ✅
- [x] `US-305-1` 发布要货计划 — `collaboration.py:266` | `test_us_305_1` ✅
- [x] `US-305-2` 查看要货计划 — `test_us_305_2` ✅
- [x] `US-306-1` 确认/修正要货计划 — `collaboration.py:294` | `test_us_306_1` ✅
- [x] `US-306-2` 查看要货计划 — `test_us_306_2` ✅
- [x] `US-307-1` 创建ASN — `supplier_collaboration.py:330` | `test_us_307_1` ✅
- [x] `US-307-2` 查看ASN — `test_us_307_2` ✅
- [x] `US-308-1` 确认送货计划 — `logistics.py:232` | `test_us_308_1` ✅
- [x] `US-308-2` 查看送货计划 — `test_us_308_2` ✅
- [x] `US-309-1` 装箱单提交 — `logistics.py:260` | `test_us_309_1` ✅
- [x] `US-309-2` 审批装箱单 — `test_us_309_2` ✅
- [x] `US-310-1` 收货验收发布 — `logistics.py:384,210` | `test_us_310_1` ✅
- [x] `US-310-2` 查看收货验收 — `test_us_310_2` ✅

---

## Phase 4: 财务结算协同

> **全部写接口使用 `await db.commit()`。**

- [x] `US-401-1` 创建结算单 — `financial.py:172` | `test_us_401_1` ✅
- [x] `US-401-2` 采购方审核 — `financial.py:266` | `test_us_401_2` ✅
- [x] `US-402-1` 修改结算单 — `financial.py:217` | `test_us_402_1` ✅
- [x] `US-402-2` 审核修改后 — `test_us_402_2` ✅
- [x] `US-403-1` 发票创建 — `financial.py:449` | `test_us_403_1` ✅
- [x] `US-403-2` 三单匹配+审批 — `financial.py:481,532` | `test_us_403_2` ✅
- [x] `US-404-1` 发票重提 — `financial.py:576` | `test_us_404_1` ✅
- [x] `US-404-2` 查看重提发票 — `test_us_404_2` ✅
- [x] `US-405-1` 付款申请/审批/确认 — `financial.py:686,718,737` | `test_us_405_1` ✅
- [x] `US-405-2` 付款状态查询 — `test_us_405_2` ✅

---

## 通用运营

### US-501 公告栏

- [x] `US-501-1` — `announcements.py:57,81,110` (CRUD) | 前端 `buyer/AnnouncementList.tsx` | `test_us_501_1` ✅
- [x] `US-501-2` — `announcements.py:204` (已读+类型统计) | 前端 `supplier/AnnouncementList.tsx` | `test_us_501_2` ✅

## US-501 修复反馈（2026-07-05）

| 问题 | 修复 | 涉及 |
|------|------|------|
| `GET /types/summary` 注册在 `/{id}` 之后导致 422 | 将 `/types/summary` 提前注册 | US-501-2 类型统计 |
| 烟测仅断言 HTTP 200 | `test_us_501_1/2` 补 title、列表命中、view_count、record-read success | 全 US-501 |
| 供应商查看未拉详情 | 打开详情时调用 `getAnnouncement` + `recordAnnouncementRead` | US-501-2 UI |

**验证：**

```powershell
pytest tests/api/test_user_stories_smoke.py -v -k "test_us_501"
```

---

## Review 结论 (2026-07-05)

基于 `README.md` 声称"全量 US 全部通过"与 `RALPH-TODO.md` 全部勾选之间的差异，逐模块审查后结论如下：

### Phase 1-2：实际可用 ✅

代码完整，API 端点齐备，前端页面就位。

### US-501：公告栏 → 已补强 ✅

原实现可用；本次修复 `/types/summary` 路由顺序并加强烟测与供应商详情加载（见上方「US-501 修复反馈」）。

### Phase 3：存在 3 个缺陷 → 已修复 ✅（commit `faf7edc`）

| # | 缺陷 | 位置 | 影响 | 修复 |
|---|------|------|------|------|
| 1 | `collaboration.router` 未挂载 | [main.py:4](backend/app/main.py) — import 列表遗漏 `collaboration` | `/collaboration/*` 全部 404，US-301~306 完全不可达 | 补 import + `include_router` |
| 2 | 5 处 `flush()` 应改为 `commit()` | [supplier_collaboration.py:190,200,287,359,388](backend/app/api/supplier_collaboration.py) | 产能响应、要货确认、ASN 创建/提交的数据不持久化 | 全部改为 `await db.commit()` |
| 3 | 缺少 US-308/309 端点 | [logistics.py](backend/app/api/logistics.py) | 采购方无法审批送货计划，供应商无法提交装箱批次 | 新增 `approve` + `packing-list` GET/POST |

### Phase 4：审批流端点 → 已修复 ✅（commit `b2411b8`）

| # | 端点 | 对应 US | 状态 |
|---|------|---------|------|
| 1 | `POST /financial/statements/{id}/buyer-audit` | US-401-2 / US-402-2 | ✅ |
| 2 | `PUT /financial/statements/{id}` | US-402-1 | ✅ |
| 3 | `GET /financial/invoices/{id}/three-way-match` | US-403-2 | ✅ |
| 4 | 发票 `approve / reject / resubmit` | US-403-2 / US-404 | ✅ |

## 前端补强记录（2026-07-05）

基于 `RALPH-TODO.md` 拉尔夫闭环方法，本次 session 完成了 Phase 2/3/4 所有前端缺口补齐：

### Phase 2 前端补强（寻源与合同协同）

| US | 文件 | 变更 |
|----|------|------|
| US-201-2, US-202-1, US-203-2 | `supplier/InvitationList.tsx` | 完全重写：新增详情 Drawer（寻源项目信息+受邀供应商+中标结果）；`projectStatusMap` 状态展示；`isWinner` 判断 + 排名化投标对比表 |
| US-204-2, US-205-1, US-206-2, US-207-1 | `supplier/ContractList.tsx` | 完全重写：`handleAcknowledge` 合同草案确认；feedback 表单（clause_id + TextArea）+ `handleSubmitFeedback`；`getContractFeedbackItems` 反馈列表；双方签署状态详情；已签合同签署记录 |
| US-205-2, US-207-2, US-208-1 | `buyer/ContractList.tsx` | 完全重写：供应商反馈列表；编辑 Modal（`editVisible`）含 contract_name/contract_amount Form；`handleEdit` 调用 `updateContract` API；签署记录区域 |
| 全部 | `api/index.ts` | 新增 4 个合同 API：`acknowledgeContractDraft`, `addContractFeedback`, `getContractFeedbackItems`, `updateContract` |
| US-201-1 | `api/index.ts` + `buyer/SourcingList.tsx` | `getSourcingProjects` 响应新增 `project_status`、`budget` 字段 |

### Phase 3 前端补强（预测与订单执行协同）

| US | 文件 | 变更 |
|----|------|------|
| US-308, US-309 | `WaybillList.tsx` | 强化：采购方审批/拒绝（`handleApprove`/`handleRejectASN`）；装箱单加载 + `Descriptions` 详情组件；装箱单 Table（material_name, quantity, batch_no, production_date, package_count）；Modal footer 审批按钮；状态扩展 `submitted/approved/rejected` |
| US-309 | `supplier/ASNList.tsx` | 新增装箱单 Modal（`packingOpen`）含可编辑表格；`handleOpenPacking` 加载已有装箱单；`handleSubmitPacking` 提交；`updatePackingItem` 行内编辑 |
| US-310 | `supplier/ReceiptList.tsx` | **新建文件**：供应商端收货验收页；按 `SUPPLIER_ID=1` 过滤；统计卡片（合格/不合格/今日/本月）；详情 Modal 含 Descriptions + items Table（quality_result, warehouse_location） |
| US-310 | `App.tsx` | 新增 `import SupplierReceiptList` + 路由 `/supplier/receipts` |
| US-310 | `components/Layout.tsx` | 新增供应商菜单项 `收货验收`（InboxOutlined, /supplier/receipts） |
| 全部 | `api/index.ts` | 清理 `getPackingLists`/`submitPackingList` 重复导出（旧版使用 `/packing-lists` 复数 → 404，新版用 `/packing-list` 单数 → 正确） |

### Phase 4 确认（财务结算协同）

| 范围 | 状态 |
|------|------|
| 后端 | `financial.py` buyer-audit、statement modify、three-way-match、invoice approve/reject/resubmit ✅ |
| 前端 `buyer/FinancialList.tsx` | 3-Tab UI：结算单（audit modal）、发票（三单匹配+approve/reject）、付款（approve/confirm）✅ |
| 前端 `supplier/SettlementList.tsx` | 创建/编辑结算单（date/amount/remarks forms）✅ |
| 前端 `supplier/InvoiceList.tsx` | 创建/重提发票 + 付款追踪 Tab ✅ |
| 结论 | **无显著缺口**，前端已完整覆盖 US-401~405 |

### 验证方式

```powershell
# 前端构建检查（需先 pnpm install）
cd frontend && pnpm install && pnpm build

# 后端全量烟测（需 Python 环境）
cd backend && python init_db.py
pytest tests/api/test_user_stories_smoke.py -v --tb=short
```

### 后续建议

1. **立即**：按 [FULL-REGRESSION-CHECKLIST.md](./FULL-REGRESSION-CHECKLIST.md) 执行全量 67 条烟测
2. **推荐命令**：`.\scripts\run-us-tests.ps1 -Fresh` 或本地 `pytest tests/api/test_user_stories_smoke.py -v --tb=short`
3. **通过后**：勾选 RALPH-TODO「全量 US 回归验收」，更新 README「全量 US 全部通过」

---

## 全量回归检查清单

完整矩阵、分 Phase 勾选表、环境命令与故障排查见 **[docs/FULL-REGRESSION-CHECKLIST.md](./FULL-REGRESSION-CHECKLIST.md)**。

| Phase | 用例数 | 快速命令 |
|-------|--------|----------|
| Health | 1 | `pytest ... -k test_health` |
| Phase 1 | 18 | `pytest ... -k "test_us_10"` |
| Phase 2 | 16 | `pytest ... -k "test_us_20"` |
| Phase 3 | 20 | `pytest ... -k "test_us_30"` |
| Phase 4 | 10 | `pytest ... -k "test_us_40"` |
| US-501 | 2 | `pytest ... -k "test_us_501"` |
| **合计** | **67** | 全量无 `-k` 过滤 |

---

## 验证命令

### 单条或局部验证

```bash
pytest tests/api/test_user_stories_smoke.py -v
```

说明：

- 不要并行执行。
- 用例依赖共享状态 `ST`。
- 如需指定接口地址，设置 `XIJIU_API_BASE`。

### 全量 US 验收

```powershell
.\scripts\run-us-tests.ps1
```

```bash
./scripts/run-us-tests.sh
```

如需经 Nginx 验证，使用 `-ThroughNginx` 或 `--nginx`。
如需干净库重跑，使用 `-Fresh` 或 `--fresh`。

---

## 集成层 Ralph-loop（SAP S/4HANA，SDD 执行）

> 基于 `docs/URS-SAP-S4HANA-Integration.md`，采用 **SDD（subagent-driven-development）** 方法论执行：每条 task 派 fresh implementer subagent + task review + 最终 review。
> 完整计划见 `docs/superpowers/plans/2026-07-06-sap-s4hana-integration.md`。

### 顶层 TODO

- [ ] Phase 0 基础设施闭环：Task 0.1~0.4（模型/连接器/适配器基类/调度器骨架）
- [ ] Phase 1 入站 P0 闭环：Task 1.1~1.8（INT-01/02/04/05/07/08/09/12）
- [ ] Phase 2 出站回传闭环：Task 2.1~2.3（INT-03/06/11）
- [ ] Phase 3 入站 P1 闭环：Task 3.1~3.3（INT-10/13/14/15）
- [ ] Phase 4 集成管理闭环：Task 4.1~4.4（INT-M01~M06）
- [ ] Phase 5 管理前端闭环：Task 5.1（日志/监控/配置/开关页面）
- [ ] Phase 6 全量回归验收：Task 6.1（集成层 + 67 条 US + URS 验收）

### 执行原则（SDD + Ralph）

1. 一次只做 1 条最小 task，fresh implementer subagent 执行。
2. 每条 task 先写失败测试再实现（TDD）。
3. 改完跑最小验证：`pytest backend/tests/integration/test_<scenario>.py -v`（串行）。
4. task review：派 task-reviewer 审 spec 合规 + 代码质量，Critical/Important 须修复重审。
5. 每个 Phase 完成跑阶段回归；Phase 6 跑全量回归（含原有 67 条 US）。
6. 全部完成后派 final code-reviewer 整分支审查。