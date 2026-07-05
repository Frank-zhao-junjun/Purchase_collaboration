# Repo Review 2026-07-05

本次 review 目标：重新核对仓库当前实现、README 宣称、US 烟测矩阵三者是否一致。

评审范围：

- `backend/app/main.py`
- `backend/app/api/*.py`
- `tests/api/test_user_stories_smoke.py`
- `README.md`

结论：当前仓库的主要风险不是代码风格，而是 **文档、测试、路由注册、实现能力不一致**。其中 Phase 3 和 Phase 4 存在阻断全量 US 验收的缺口。

---

## Findings

### 1. High - `/collaboration/*` 路由未挂载，Phase 3 采购侧主链会直接 404

现象：

- `backend/app/api/collaboration.py` 已实现 `/collaboration/forecasts`、`/collaboration/delivery-schedules` 等接口。
- 但 `backend/app/main.py` 没有 `app.include_router(collaboration.router)`。
- 当前只挂载了 `supplier_collaboration.router`。

影响：

- US-301 ~ US-306 的采购侧接口在默认应用入口下不可用。
- `tests/api/test_user_stories_smoke.py` 中对应用例会直接失败，而不是业务断言失败。

证据：

- `backend/app/main.py`
- `backend/app/api/collaboration.py`
- `tests/api/test_user_stories_smoke.py` 中 `/collaboration/forecasts*`
- `tests/api/test_user_stories_smoke.py` 中 `/collaboration/delivery-schedules*`

建议：

- 先修复应用挂载问题，再跑 Phase 3 最小烟测。

---

### 2. High - 财务模块接口面不满足 US-401 ~ US-404 的烟测与验收路径

现象：

- 当前 `financial.py` 只具备结算单创建、确认、发票创建、付款创建/审批/支付等基础接口。
- 缺少烟测明确依赖的以下能力：
  - `POST /financial/statements/{id}/buyer-audit`
  - `PUT /financial/statements/{id}`
  - `GET /financial/invoices/{id}/three-way-match`
  - `POST /financial/invoices/{id}/approve`
  - `POST /financial/invoices/{id}/reject`
  - `POST /financial/invoices/{id}/resubmit`

影响：

- Phase 4 主链无法按 README 所述“全部通过”。
- 财务闭环目前只覆盖了最薄的 CRUD，而非 PRD/US 需要的审核与驳回重提流程。

证据：

- `backend/app/api/financial.py`
- `tests/api/test_user_stories_smoke.py` 中 `buyer-audit`
- `tests/api/test_user_stories_smoke.py` 中 `three-way-match`
- `tests/api/test_user_stories_smoke.py` 中 `approve/reject/resubmit`

建议：

- 以 `US-401-2`、`US-402-1`、`US-403-2`、`US-404-1` 为优先顺序补足状态机与接口。

---

### 3. High - 物流模块缺少 US-308/309 所需接口，且状态机与烟测不一致

现象：

- 当前 `logistics.py` 的 `/shipment-notes/` 创建时即写入 `submitted` 状态。
- 已实现 `arrive`，但没有实现烟测调用的：
  - `POST /logistics/shipment-notes/{id}/submit`
  - `POST /logistics/shipment-notes/{id}/approve`
  - `POST /logistics/shipment-notes/{id}/packing-lists`
  - `GET /logistics/shipment-notes/{id}/packing-lists`

影响：

- US-307 ~ US-309 无法形成“创建 -> 提交 -> 采购确认 -> 装箱批次 -> 审批”的闭环。
- 当前实现和 README/烟测所表达的业务状态流转不一致。

证据：

- `backend/app/api/logistics.py`
- `tests/api/test_user_stories_smoke.py` 中 `shipment-notes/{id}/submit`
- `tests/api/test_user_stories_smoke.py` 中 `shipment-notes/{id}/approve`
- `tests/api/test_user_stories_smoke.py` 中 `packing-lists`

建议：

- 先统一 ASN/Shipment Note 的状态机，再补最小接口面，不要继续让创建接口直接跳过提交态。

---

### 4. Medium - `supplier_collaboration.py` 多个写接口只 `flush` 不 `commit`

现象：

- 产能响应更新/创建
- 要货计划确认
- ASN 创建
- ASN 提交

这些路径在返回成功前只调用 `await db.flush()`，没有 `await db.commit()`。

影响：

- 接口返回 200/成功消息，但数据持久化依赖会话生命周期，行为不稳定。
- 后续请求可能读不到刚写的数据，尤其影响串行烟测和页面刷新后的结果一致性。

证据：

- `backend/app/api/supplier_collaboration.py`

建议：

- 所有会改变业务状态的写接口统一补 `commit`，并在需要时重新查询返回最终状态。

---

### 5. Medium - README 的“全量 US 全部通过”声明与当前实现不一致

现象：

- README 明确写出 Phase 1 ~ 4 和 US-501 均“全部通过”。
- 但当前默认应用入口下，至少 Phase 3 和 Phase 4 无法满足烟测依赖的接口面。

影响：

- 会误导后续验收、排障和迭代判断。
- 导致团队误以为问题只在测试环境，而不是实现未闭环。

证据：

- `README.md` 中“全量 US 测试结果”表格

建议：

- 在修复前临时下调声明，或补充“当前主分支待恢复 Phase 3/4 US 回归”的说明。

---

## 修复优先级 TODO

### P0 - 先恢复可运行主链

1. 在 `backend/app/main.py` 注册 `collaboration.router`
2. 跑 Phase 3 的 `/collaboration/*` 最小烟测，确认不再 404
3. 梳理 `logistics.py` 的 Shipment Note / ASN 状态机
4. 补齐 `submit`、`approve`、`packing-lists` 相关接口
5. 梳理 `financial.py` 的结算单/发票状态机
6. 补齐 `buyer-audit`、结算单修改、三单匹配、发票审批/驳回/重提接口

### P1 - 修复写入一致性

1. 给 `supplier_collaboration.py` 的所有写接口补 `commit`
2. 对返回值改为基于提交后重新查询的数据
3. 跑 Phase 3 相关烟测，确认串行状态稳定

### P1 - 校正文档和验收基线

1. 更新 README 的测试结果说明，避免继续声称“全部通过”
2. 把当前 review 结论链接到 Ralph-loop 工作清单
3. 将修复顺序映射回最小 US

### P2 - 完整回归

1. 先跑 Phase 3 局部回归
2. 再跑 Phase 4 局部回归
3. 最后执行全量 `run-us-tests` 验收

---

## 推荐执行顺序

建议不要从 Phase 1 重新开始，因为当前最大的阻断不在那里。

推荐顺序：

1. `US-301-1 ~ US-306-2`
2. `US-307-1 ~ US-309-2`
3. `US-401-1 ~ US-404-2`
4. `US-405-1 ~ US-405-2`
5. README 与全量回归

这样做的原因：

- 先修路由挂载与缺失接口，能最快恢复“烟测可跑”。
- 再修事务提交问题，能保证 Phase 3 行为稳定。
- 最后再回头校正文档，不会出现“文档刚改完又被代码推翻”。
