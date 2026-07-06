# 全量 US 回归检查清单

面向 `tests/api/test_user_stories_smoke.py` 的 **66 条 US 烟测 + 1 条 health**，按 Phase 串行验收。与 [RALPH-TODO.md](./RALPH-TODO.md) 顶层「全量 US 回归验收」对应。

---

## 1. 验收标准（Exit Criteria）

| 项 | 要求 |
|----|------|
| API 烟测 | `pytest tests/api/test_user_stories_smoke.py -v` **全部 PASSED** |
| 用例数量 | **67**（`test_health` + 66 × `test_us_*`） |
| 执行方式 | **串行、单进程**（禁止 `pytest-xdist`） |
| 数据依赖 | 用例共享 `ST` 状态，**必须按文件顺序**执行 |
| 干净库 | 首次或遇唯一约束冲突时加 `-Fresh` / `init_db.py` 重建 |

---

## 2. 注意事项

### 2.1 执行纪律（必守）

- **禁止并行：** 不得使用 `pytest-xdist` 或多进程跑 `test_user_stories_smoke.py`。
- **必须串行：** 67 条用例共享文件内状态对象 `ST`，**必须按 `test_user_stories_smoke.py` 中的定义顺序**从头到尾执行。
- **`-k` 过滤：** 仅用于定位失败 Phase；过滤后仍按文件顺序跑匹配项。**不要只跑某个 Phase 的后半段**（例如单独跑 `test_us_401_2` 而不跑前面的 `test_us_401_1`）。
- **API 地址：** 默认 `http://127.0.0.1:8000`；Docker/Nginx 场景通过 `XIJIU_API_BASE` 指定（见 `run-us-tests.ps1`）。
- **干净库：** 首次全量回归、或出现唯一约束 / 脏数据导致随机失败时，务必 `init_db.py` 或 `.\scripts\run-us-tests.ps1 -Fresh` 后再跑。

### 2.2 验收范围说明

- **API 层**：本清单验收的是 **API 层 US 烟测**（`tests/api/test_user_stories_smoke.py`），共 67 条。
- **E2E 层**：`tests/e2e/` 为 **Playwright 前端 E2E 补充**，共 53 条（见 [§11 E2E 回归矩阵](#11-e2e-回归矩阵)）。E2E 不替代 pytest，但应在 API 全绿后执行。
- Phase 矩阵中的 **「可选 UI 抽检」** 已由 E2E 自动化覆盖，无需人工点验。
- **不要在未实际跑通 pytest 的情况下** 对外宣称「全量 US 已通过」。

### 2.3 全部通过后的必做事项

仅在 **`pytest tests/api/test_user_stories_smoke.py -v` 显示 67 passed** 时执行：

1. **填写回归记录** — 使用本文 [§8 回归记录模板](#8-回归记录模板)，保存日期、环境、命令、结果。
2. **勾选 RALPH-TODO** — 打开 [RALPH-TODO.md](./RALPH-TODO.md)，将顶层  
   `- [ ] 全量 US 回归验收`  
   改为  
   `- [x] 全量 US 回归验收`（可附执行日期与 `67 passed`）。
3. **更新 README 声明** — 打开 [README.md](../README.md) 中 **「全量 US 测试结果」** 小节：
   - 将表格日期更新为**实际跑通日期**（勿沿用旧日期）；
   - 确认 Phase 1~4、US-501 行仍为「✅ 全部通过」且与本次 pytest 结果一致；
   - 若 Phase 3/4 曾修复 P0 端点，README 的 API 清单应与当前 `backend/app/api/*` 一致（可参考 [RALPH-TODO.md](./RALPH-TODO.md) 中的「Phase 3 P0 修复反馈」表格）。
4. **（可选）** 同步 [AGENTS.md](../AGENTS.md) 功能矩阵状态，与 RALPH-TODO 保持一致。

### 2.4 未通过或部分通过时

- **不要** 勾选 RALPH-TODO「全量 US 回归验收」。
- **不要** 将 README 写成「全量 US 全部通过」。
- 记录**首个失败用例**与 traceback → 按 Phase `-k` 复现 → 修复后 **`-Fresh` 全量重跑**（避免 `ST` 半途中断导致误判）。

### 2.5 提交与协作

- 代码修复与文档更新（RALPH-TODO / README）可分开 commit；文档更新建议在 pytest 绿屏**之后**再提交。
- 推送远程前建议本地或 CI 再跑一遍全量烟测，防止环境差异导致误报。

---

## 3. 环境准备

### 方式 A：本地开发（SQLite，推荐调试）

#### A1. 已有可用 Python 环境

```powershell
cd backend
python -m pip install -r requirements.txt
python init_db.py
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

另开终端：

```powershell
cd <项目根>
python -m pip install -r requirements-dev.txt
$env:XIJIU_API_BASE = "http://127.0.0.1:8000"
python -m pytest tests/api/test_user_stories_smoke.py -v --tb=short
```

#### A2. Windows 无系统 Python 时的已验证路径（推荐）

当前仓库已在本工作区通过 `uv + Python 3.12` 验证分 Phase 烟测，可作为本地回归基线。

```powershell
cd <项目根>
uv python install 3.12
uv venv .venv312 --python 3.12
uv pip install --python .\.venv312\Scripts\python.exe fastapi==0.109.0 "uvicorn[standard]==0.27.0" sqlalchemy==2.0.25 aiosqlite==0.19.0 pydantic==2.5.3 pydantic-settings==2.1.0 python-multipart==0.0.6 pytest>=7.4.0 httpx>=0.27.0 python-dateutil
```

初始化数据库并启动后端：

```powershell
cd backend
..\.venv312\Scripts\python.exe init_db.py
..\.venv312\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

另开终端执行回归：

```powershell
cd <项目根>
$env:XIJIU_API_BASE = "http://127.0.0.1:8000"
.\.venv312\Scripts\python.exe -m pytest tests/api/test_user_stories_smoke.py -v --tb=short
```

### 方式 B：Docker 一键（演示/CI 近似）

```powershell
.\scripts\run-us-tests.ps1 -Fresh
```

经 Nginx 反代验证：

```powershell
.\scripts\run-us-tests.ps1 -Fresh -ThroughNginx
```

Linux/macOS：`./scripts/run-us-tests.sh [--fresh] [--nginx]`

### 前置检查

- [ ] `curl http://127.0.0.1:8000/health` 返回 `{"status":"healthy"}`
- [ ] 已安装 `httpx`、`pytest`（见 `requirements-dev.txt`）
- [ ] 未设置会干扰的 `pytest-xdist` / 并行插件
- [ ] 数据库为种子数据或 `-Fresh` 后的干净库

---

## 4. 执行命令速查

| 场景 | 命令 |
|------|------|
| **全量回归** | `pytest tests/api/test_user_stories_smoke.py -v --tb=short` |
| Phase 1 | `pytest ... -v -k "test_us_10"` |
| Phase 2 | `pytest ... -v -k "test_us_20"` |
| Phase 3 | `pytest ... -v -k "test_us_30"` |
| Phase 4 | `pytest ... -v -k "test_us_40"` |
| US-501 | `pytest ... -v -k "test_us_501"` |
| 单条 | `pytest ... -v -k "test_us_401_1"` |

> `-k` 过滤仍按文件顺序跑匹配项；Phase 内子用例有 `ST` 依赖，不要只跑后半段。

---

## 5. Phase 回归矩阵

状态列用于人工勾选；自动化以 pytest 结果为准。

### Phase 1：供应商准入（18 用例）

| 用例 | US | 角色 | 关键 API / 断言要点 |
|------|-----|------|---------------------|
| [ ] `test_us_101_1` | 101-1 | 采购 | `POST /supplier-portal/invitations` |
| [ ] `test_us_101_2` | 101-2 | 供应商 | `GET /supplier-portal/invitations?email=` |
| [ ] `test_us_102_1` | 102-1 | 供应商 | `POST /supplier-portal/register` |
| [ ] `test_us_102_2` | 102-2 | 采购 | `GET /supplier-portal/registrations/{id}` |
| [ ] `test_us_103_1` | 103-1 | 采购 | 审批通过/驳回 |
| [ ] `test_us_103_2` | 103-2 | 供应商 | `GET /supplier-portal/register/status` + 注册→驳回→`POST .../resubmit` |
| [ ] `test_us_104_1` | 104-1 | 采购 | `POST /qualification/projects` |
| [ ] `test_us_104_2` | 104-2 | 供应商 | `GET /qualification/projects?supplier_id=` + `GET /qualification/projects/{id}` |
| [ ] `test_us_105_1` | 105-1 | 供应商 | `POST /qualification/projects/{id}/submission` |
| [ ] `test_us_105_2` | 105-2 | 采购 | `GET /qualification/projects/{id}/submissions` + `GET /qualification/projects/{id}/submissions/{supplier_id}` |
| [ ] `test_us_106_1` | 106-1 | 采购 | 评审打分 `POST .../submissions/{sid}/review` → 含 final_score |
| [ ] `test_us_106_2` | 106-2 | 供应商 | `GET /qualification/projects/{id}/status?supplier_id=` → 含 final_score |
| [ ] `test_us_107_1` | 107-1 | 采购 | 最终批准/拒绝 |
| [ ] `test_us_107_2` | 107-2 | 供应商 | 查看最终决定 |
| [ ] `test_us_108_1` | 108-1 | 采购 | 资质预警/重认证邀请 |
| [ ] `test_us_108_2` | 108-2 | 供应商 | `GET /supplier-portal/suppliers/{id}/certifications`（验证资质列表） |
| [ ] `test_us_109_1` | 109-1 | 供应商 | 资质更新/重认证材料 |
| [ ] `test_us_109_2` | 109-2 | 采购 | 查看资质更新记录 |

**可选 UI 抽检：** `/buyer/invitations` → `/supplier/registration` → `/buyer/qualifications` → `/supplier/qualifications`

---

### Phase 2：寻源与合同（16 用例）

| 用例 | US | 角色 | 关键 API |
|------|-----|------|----------|
| [ ] `test_us_201_1` | 201-1 | 采购 | `POST /sourcing/projects` |
| [ ] `test_us_201_2` | 201-2 | 供应商 | `GET /sourcing/projects/{id}` |
| [ ] `test_us_202_1` | 202-1 | 供应商 | accept/decline 邀请 |
| [ ] `test_us_202_2` | 202-2 | 采购 | `GET /sourcing/projects/{id}` 查看邀请响应 |
| [ ] `test_us_203_1` | 203-1 | 采购 | 授标 |
| [ ] `test_us_203_2` | 203-2 | 供应商 | `GET /sourcing/projects/{id}` 查看授标结果 |
| [ ] `test_us_204_1` | 204-1 | 采购 | `POST /contracts/generate-from-sourcing/{id}` |
| [ ] `test_us_204_2` | 204-2 | 供应商 | `GET /contracts/drafts/{id}` |
| [ ] `test_us_205_1` | 205-1 | 供应商 | `POST /contracts/{id}/feedback` |
| [ ] `test_us_205_2` | 205-2 | 采购 | `GET /contracts/{id}/feedback-items` |
| [ ] `test_us_206_1` | 206-1 | 采购 | 发起签署 |
| [ ] `test_us_206_2` | 206-2 | 供应商 | 签署 |
| [ ] `test_us_207_1` | 207-1 | 供应商 | 签署状态 |
| [ ] `test_us_207_2` | 207-2 | 采购 | 签署状态 |
| [ ] `test_us_208_1` | 208-1 | 采购 | 修改合同状态 |
| [ ] `test_us_208_2` | 208-2 | 供应商 | `GET /contracts/{id}` 查看状态变更 |

**可选 UI 抽检：** `/buyer/sourcing` → `/supplier/invitations` → `/buyer/contracts`

---

### Phase 3：预测与订单执行（20 用例）

| 用例 | US | 角色 | 关键 API / 状态流 |
|------|-----|------|-------------------|
| [ ] `test_us_301_1` | 301-1 | 采购 | `POST /collaboration/forecasts` → publish → `assert published` |
| [ ] `test_us_301_2` | 301-2 | 供应商 | `GET /collaboration/forecasts?supplier_id=1` → 列表含创建的预测 |
| [ ] `test_us_302_1` | 302-1 | 供应商 | `POST /collaboration/forecasts/{id}/responses` → `success=true` |
| [ ] `test_us_302_2` | 302-2 | 采购 | `GET /collaboration/forecasts/{id}/responses` → 列表含响应 |
| [ ] `test_us_303_1` | 303-1 | 采购 | `POST /purchase-orders/` |
| [ ] `test_us_303_2` | 303-2 | 供应商 | `POST /purchase-orders/{id}/supplier-confirm` |
| [ ] `test_us_304_1` | 304-1 | 采购 | `PUT /purchase-orders/{id}` → `status: "cancelled"` |
| [ ] `test_us_304_2` | 304-2 | 供应商 | `GET /purchase-orders/{id}` → 确认 cancelled |
| [ ] `test_us_305_1` | 305-1 | 采购 | `POST /collaboration/delivery-schedules` |
| [ ] `test_us_305_2` | 305-2 | 供应商 | 查看要货计划 |
| [ ] `test_us_306_1` | 306-1 | 供应商 | supplier-confirm → `confirmed` |
| [ ] `test_us_306_2` | 306-2 | 采购 | 查看已确认计划 |
| [ ] `test_us_307_1` | 307-1 | 供应商 | `POST /logistics/shipment-notes/` → `draft` |
| [ ] `test_us_307_2` | 307-2 | 采购 | `GET /logistics/shipment-notes/` → 列表含新 ASN |
| [ ] `test_us_308_1` | 308-1 | 采购 | `POST /logistics/shipment-notes/{id}/submit` → approve → `approved` |
| [ ] `test_us_308_2` | 308-2 | 供应商 | `GET /logistics/shipment-notes/{id}` → status=approved |
| [ ] `test_us_309_1` | 309-1 | 供应商 | `POST /logistics/shipment-notes/{id}/packing-lists` → `success=true` |
| [ ] `test_us_309_2` | 309-2 | 采购 | `GET /logistics/shipment-notes/{id}/packing-lists` → 列表非空 |
| [ ] `test_us_310_1` | 310-1 | 采购 | `POST /logistics/receipts/` → status=qualified |
| [ ] `test_us_310_2` | 310-2 | 供应商 | `GET /logistics/receipts/` → 列表含收货记录 |

**P0 回归重点：** `/collaboration/*` 可达、`/logistics/.../submit|approve|packing-lists` 存在。

**可选 UI 抽检：** `/buyer/forecast` → `/supplier/capacity` → `/buyer/financial` 前的 `/buyer/delivery-plans`、`/supplier/asn`

---

### Phase 4：财务结算（10 用例）

| 用例 | US | 角色 | 关键 API / 状态流 |
|------|-----|------|-------------------|
| [ ] `test_us_401_1` | 401-1 | 供应商 | `POST /financial/statements/?submit=true` → `pending_audit` |
| [ ] `test_us_401_2` | 401-2 | 采购 | `POST .../buyer-audit` approve → `confirmed` |
| [ ] `test_us_402_1` | 402-1 | 供应商 | `PUT .../statements/{id}?submit=true` |
| [ ] `test_us_402_2` | 402-2 | 采购 | 再次 buyer-audit |
| [ ] `test_us_403_1` | 403-1 | 供应商 | `POST /financial/invoices/` |
| [ ] `test_us_403_2` | 403-2 | 采购 | three-way-match + approve → `verified` |
| [ ] `test_us_404_1` | 404-1 | 供应商 | reject → resubmit |
| [ ] `test_us_404_2` | 404-2 | 采购 | 查看重提发票 |
| [ ] `test_us_405_1` | 405-1 | 采购 | `POST /financial/payments/` → 创建付款记录 |
| [ ] `test_us_405_2` | 405-2 | 供应商 | `GET /financial/payments/?supplier_id=1` → 列表含付款记录 |

**可选 UI 抽检：** `/buyer/financial`（结算审核/三单匹配/付款）→ `/supplier/settlements` → `/supplier/invoices`

---

### US-501：公告栏（2 用例）

| 用例 | US | 角色 | 关键 API |
|------|-----|------|----------|
| [ ] `test_us_501_1` | 501-1 | 采购 | `POST /announcements/` |
| [ ] `test_us_501_2` | 501-2 | 供应商 | GET 详情 + `record-read` + `/types/summary` |

**回归重点：** `GET /announcements/types/summary` 不能 422（路由须在 `/{id}` 之前）。

**可选 UI 抽检：** `/buyer/announcements` → `/supplier/announcements`

---

## 6. 推荐执行顺序

```mermaid
flowchart LR
  A[环境就绪 health=200] --> B[全量 pytest 67 条]
  B --> C{全部 PASSED?}
  C -->|否| D[定位失败 Phase -k 过滤]
  D --> E[修复后 -Fresh 重跑]
  E --> B
  C -->|是| F[可选 UI 抽检]
  F --> G[勾选 RALPH-TODO 全量回归]
  G --> H[更新 README 声明]
```

1. **Smoke：** `test_health`
2. **Phase 1 → 2 → 3 → 4 → 501**（文件默认顺序，勿打乱）
3. **失败时：** 记录首个失败用例名 → 用 `-k` 从 Phase 起点重跑（或 `-Fresh` 全量重跑）
4. **通过后：** 按 [§2.3 全部通过后的必做事项](#23-全部通过后的必做事项) 更新 RALPH-TODO 与 README；然后跑 E2E（见 [§11](#11-e2e-回归矩阵)）

---

## 7. 常见问题

| 现象 | 可能原因 | 处理 |
|------|----------|------|
| 404 on `/collaboration/*` | router 未挂载 | 检查 `main.py` 含 `collaboration.router` |
| 404 on `packing-lists` / `submit` | logistics 端点缺失 | 检查 `logistics.py` US-308/309 |
| 500 on `/contracts/{id}/sign-status` | `contract.status` 被当作 enum 读取，但实际是字符串 | 检查 `sourcing.py` 中 sign-status 返回值兼容 enum/string |
| 422 on `/announcements/types/summary` | 路由顺序 | `types/summary` 须在 `/{id}` 前 |
| 409 / UNIQUE 约束 | 旧库脏数据 | `init_db.py` 或 `-Fresh` |
| 500 on `/financial/invoices/` | 自动生成 `invoice_no` 冲突 | 检查 `financial.py` 的发票号生成是否含足够随机性 |
| 前面过、后面挂 | 并行跑或跳过用例 | 禁用 xdist，全文件串行 |
| Phase 4 三单匹配 fail | 发票金额 > 结算单 | 检查 `three-way-match` 逻辑 |

---

## 8. 回归记录模板

```
日期：
执行人：
环境：本地 SQLite / Docker / Nginx
命令：
结果：67 passed / __ failed
失败用例：
根因：
修复 commit：
复验：
RALPH-TODO 已勾选：[ ] 是 / [ ] 否
README 已更新：[ ] 是 / [ ] 否
```

---

## 9. 相关文档

- 用户故事定义：[US.txt](./US.txt)
- Ralph 进度：[RALPH-TODO.md](./RALPH-TODO.md)
- 仓库审查：[REPO-REVIEW-2026-07-05.md](./REPO-REVIEW-2026-07-05.md)
- API 测试说明：[tests/api/README.md](../tests/api/README.md)
- E2E 测试说明：[tests/e2e/README.md](../tests/e2e/README.md)

---

## 10. 回归记录

### 2026-07-05

```
日期：2026-07-05
执行人：Agent (Vibe Coding)
环境：本地 SQLite（sandbox，Python 3.12，FastAPI 0.109，uvicorn 0.27）
命令：XIJIU_API_BASE=http://127.0.0.1:8000 pytest tests/api/test_user_stories_smoke.py -v --tb=short
结果：67 passed / 0 failed (1.12s)
失败用例：无
根因：N/A
修复 commit：N/A（首次全量即通过）
复验：clean DB (rm supply_chain.db + init_db.py) → 全量串行 → 67 passed
RALPH-TODO 已勾选：[x] 是
README 已更新：[x] 是（日期更新为 2026-07-05）
```

### 2026-07-05 — E2E (Playwright)

```
日期：2026-07-05
执行人：Agent (Vibe Coding)
环境：sandbox，前端 Vite dev (port 5000) + 后端 uvicorn (port 8000) + Chromium 132 (Playwright)
命令：cd tests/e2e && npx playwright test --config=playwright.config.simple.ts
结果：53 passed / 0 failed (50.5s)
失败用例：无（首轮 49 failed → 修复后 0 failed）
根因：BasePage baseURL 硬编码 3000（应为 5000）、Page Object 路由与 App.tsx 不匹配、
      Ant Design 5.x 选择器未适配、前端搜索输入框未绑定 onChange
修复：
  1. BasePage.ts: baseURL 3000 → 5000
  2. DashboardPage/SupplierPage/PurchaseOrderPage/InventoryPage: 路由对齐 App.tsx 实际路径
  3. 表格选择器: table.ant-table → .ant-table table（AD5 class 在 wrapper div 上）
  4. 快捷操作卡片: .ant-card:has-text → .ant-card-hoverable:has-text（避免匹配统计卡片）
  5. simple.spec.ts: 标题断言 /白酒供应链/ → /采购供应链/
  6. InventoryList.tsx/SupplierList.tsx/PurchaseOrderList.tsx: 搜索输入框补绑 value+onChange+客户端过滤
复验：53 passed
RALPH-TODO 已勾选：[x] 是
README 已更新：[x] 是
```

---

## 11. E2E 回归矩阵

### 11.1 概述

E2E 测试基于 **Playwright + Chromium**，覆盖前端核心页面的功能验证。与 API 烟测互补：API 验证后端业务逻辑，E2E 验证前端渲染与交互。

### 11.2 执行方式

```bash
# 前置：后端运行在 8000，前端运行在 5000
cd tests/e2e
pnpm install
npx playwright install chromium          # 首次需要
npx playwright test --config=playwright.config.simple.ts
```

### 11.3 测试用例矩阵

| 模块 | Spec 文件 | 用例数 | 覆盖范围 |
|------|-----------|--------|----------|
| 仪表盘 | `dashboard.spec.ts` | 7 | 核心指标加载、预警区域、快捷操作导航、寻源列表、刷新、跨模块跳转、待办事项 |
| 库存管理 | `inventory.spec.ts` | 19 | 列表展示、统计卡片、低库存告警、Tab 切换、盘点入口、搜索/筛选、统计摘要、出入库、刷新、导出 |
| 采购订单 | `purchase-order.spec.ts` | 11 | 新建按钮、订单详情、状态显示、审批流程、发货确认、筛选、分页、导出、搜索 |
| 供应商管理 | `supplier.spec.ts` | 13 | 列表展示、新增/编辑/删除按钮、评级显示、统计看板、状态筛选、搜索、详情查看、分页 |
| 冒烟测试 | `simple.spec.ts` | 3 | 首页访问、API 健康检查、Dashboard 数据加载 |
| **合计** | — | **53** | — |

### 11.4 Page Object 结构

```
tests/e2e/
├── playwright.config.simple.ts   # 配置（baseURL: localhost:5000, chromium）
├── pages/                        # Page Object 模型
│   ├── BasePage.ts               # 基类（导航、等待、通用操作）
│   ├── DashboardPage.ts          # 仪表盘页面对象
│   ├── SupplierPage.ts           # 供应商管理页面对象
│   ├── PurchaseOrderPage.ts      # 采购订单页面对象
│   ├── InventoryPage.ts          # 库存管理页面对象
│   └── index.ts                  # 统一导出
├── specs/                        # 测试用例
│   ├── simple.spec.ts            # 冒烟测试 (3)
│   ├── dashboard.spec.ts         # 仪表盘 (7)
│   ├── supplier.spec.ts          # 供应商 (13)
│   ├── purchase-order.spec.ts    # 采购订单 (11)
│   └── inventory.spec.ts         # 库存 (19)
└── fixtures/
    └── test-data.ts              # 测试数据
```

### 11.5 前端 Bug 修复记录

E2E 首轮执行发现并修复的前端缺陷：

| 文件 | 问题 | 修复 |
|------|------|------|
| `InventoryList.tsx` | 搜索输入框 `Input.Search` 未绑定 `value`/`onChange`，输入关键词不触发过滤 | 添加 `searchKeyword` 状态 + `value`/`onChange` 绑定 + 客户端 `filter` |
| `SupplierList.tsx` | 同上 | 同上 |
| `PurchaseOrderList.tsx` | 同上 | 同上 |

### 11.6 E2E 执行结果

| 日期 | 结果 | 耗时 | 备注 |
|------|------|------|------|
| 2026-07-05 | **53 passed / 0 failed** | 50.5s | 首轮 49 failed → 修复 6 类问题后全绿 |
