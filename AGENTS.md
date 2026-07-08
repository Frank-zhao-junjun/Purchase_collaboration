# 白酒供应链数字化管控平台 - AGENTS.md

## 项目概览

面向白酒企业的供应链全链路数字化管控系统 Demo，聚焦"采购→到货验收→入库→库存管理"核心链路。

## 默认 LLM 模型

- **模型**: DeepSeek V4 Flash (deepseek-v4-flash)
- **用途**: 本项目的所有开发、代码生成、分析、审查任务默认使用此模型
- **覆盖规则**: 如特定任务需使用其他模型（如 DeepSeek Chat），可在具体需求中显式指定

## 默认开发标准（Agent Skills Plugin）

本项目默认采用 Agent Skills 作为后续开发标准，已安装到项目目录 `.agents/skills/`。

执行规则：

1. 任何需求改动先走 spec-driven-development（先规格后实现）。
2. 所有功能与缺陷修复默认执行 test-driven-development（先测试后实现）。
3. 提交前必须执行 code-review-and-quality 与 debugging-and-error-recovery 的检查清单。
4. 涉及接口边界时必须遵循 api-and-interface-design。
5. 涉及安全、性能、上线发布时，分别执行 security-and-hardening、performance-optimization、shipping-and-launch。

推荐命令流：/spec → /plan → /build → /test → /review → /ship。


## 功能责任矩阵（US Checklist & 责任分工）

本表同步自 prd.json/PRD.md，明确每个用户故事（US）的采购端/供应商端/外部系统责任分工及完成状态。

| US编号 | 标题 | 采购端实质操作 | 供应商端实质操作 | 外部系统同步来源 | 状态 |
|--------|------|----------------|------------------|------------------|------|
| US-101 | 供应商注册邀请 | 发起注册邀请、维护邀请对象、发送注册链接 | 无 | 无 | ✅ |
| US-102 | 供应商自助注册 | 无 | 填写注册信息、提交企业资料 | 无 | ✅ |
| US-103 | 供应商注册状态查询 | 审核注册申请、批准或驳回、维护驳回原因 | 按驳回意见补充资料并重新提交 | 无 | ✅ |
| US-104 | 供应商资格评审项目创建 | 创建资格评审项目、选择目标供应商、发布评审要求 | 无 | 无 | ✅ |
| US-105 | 供应商在线填写资格问卷 | 无 | 填写资格问卷、上传资质文件、补充提交材料 | 无 | ✅ |
| US-106 | 采购方评审资格文件 | 组织多角色评审、发起澄清、提交评审意见 | 回复澄清、补交材料 | 无 | ✅ |
| US-107 | 资格申请状态协同 | 最终批准或拒绝资格申请、维护审批原因 | 补充材料后重新申请 | 无 | ✅ |
| US-108 | 供应商资质过期预警与重认证 | 无 | 更新资质有效期、提交重认证材料 | 资质到期预警和重认证草稿由系统自动触发 | ✅ |
| US-201 | 寻源项目发布 | 创建寻源项目、邀请供应商 | 接收邀请 | 寻源项目、邀请范围、评审标准等由 SRM/寻源系统同步 | ✅ |
| US-202 | 供应商接收/拒绝邀请 | 无 | 接受或拒绝寻源邀请、填写拒绝原因 | 邀请通知由 SRM/寻源系统同步，响应结果回传采购侧系统 | ✅ |
| US-203 | 供应商在线投标报价 | 无 | 提交投标报价、上传技术方案、参与多轮报价 | 寻源项目基础信息由 SRM/寻源系统同步 | ✅ |
| US-204 | 采购方在线开标比价 | 开标、查看比价表 | 根据澄清要求补充说明或更新报价 | 开标结果、比价表、澄清公告由 SRM/寻源系统同步 | ✅ |
| US-205 | 中标/落标通知发布 | 授标 | 无 | 授标结果由 SRM/寻源系统同步 | ✅ |
| US-206 | 合同草案发布 | 基于授标生成合同、发起签署 | 查收合同草案 | 合同草案、条款模板和主数据由合同系统或 SRM 同步 | ✅ |
| US-207 | 合同修改意见反馈 | 无 | 逐条提交合同修改意见、补充说明或附件 | 采购侧对修改意见的处理结果由合同系统同步 | ✅ |
| US-208 | 合同在线签署 | 采购方签署 | 在线签署合同、完成签署确认 | 签署任务和签署顺序由合同系统或电子签系统同步 | ✅ |
| US-209 | 合同状态协同 | 无 | 无 | 合同状态、签署结果和生效结果由合同系统或电子签系统同步 | ✅ |
| US-301 | 采购预测发布 | 查看预测数据 | 无 | 采购预测由 ERP/计划系统同步 | ✅ |
| US-302 | 供应商产能响应 | 无 | 提交产能响应、交期承诺、风险说明 | 采购预测基础数据由 ERP/计划系统同步，响应结果回传采购侧系统 | ✅ |
| US-303 | 采购订单发布与接收 | 无 | 确认订单、拒绝订单、提出异议 | 采购订单由 ERP 同步，处理结果回传采购侧系统 | ✅ |
| US-304 | 采购订单变更与关闭 | 无 | 无 | 订单变更、关闭和取消结果由 ERP 同步 | ✅ |
| US-305 | 要货计划发布 | 查看要货计划 | 无 | 要货计划由 ERP 或计划系统同步 | ✅ |
| US-306 | 供应商确认/修正要货计划 | 无 | 确认要货计划、提交调整建议 | 要货计划基础数据由 ERP/计划系统同步，处理结果回传采购侧系统 | ✅ |
| US-307 | 供应商创建送货计划 (ASN) | 无 | 创建 ASN、维护发货信息 | 已确认要货计划由 ERP/计划系统同步 | ✅ |
| US-308 | 采购方确认送货计划 | 批准、拒绝、修改送货计划 | 根据采购侧处理结果确认或调整送货安排 | ASN 基础数据由供应商在本系统提交 | ✅ |
| US-309 | 装箱单与批次信息提交 | 批准、拒绝、修改装箱单与批次信息 | 提交装箱单与批次信息，并按意见修改 | ASN 基础数据来自本系统，入库关联结果由 WMS/QMS 同步 | ✅ |
| US-310 | 收货与验收结果发布 | 确认到货、创建入库单 | 无 | 收货单和质检结果由 WMS/QMS 同步 | ✅ |
| US-401 | 供应商创建结算单 | 无 | 创建结算单、提交对账信息 | 已收货且未结算记录由 ERP/WMS/QMS 同步 | ✅ |
| US-402 | 采购方审核结算单 | 批准、拒绝、留言 | 根据意见修订结算单、回复留言 | 收货明细和应付基础数据由 ERP/WMS/QMS 同步 | ✅ |
| US-403 | 发票创建与上传 | 无 | 创建发票、上传发票影像 | 已确认结算单和财务主数据由 ERP/财务系统同步 | ✅ |
| US-404 | 采购方三单匹配与发票审批 | 查看三单匹配结果、批准或拒绝发票 | 按驳回原因补充说明或重提发票 | 订单、收货和发票基础数据由 ERP/WMS/财务系统同步 | ✅ |
| US-405 | 付款状态发布与查询 | 审批付款、确认付款 | 无 | 付款记录和付款状态由财务系统同步 | ✅ |
| US-501 | 公告栏运营协同 | 发布、编辑、删除公告 | 查看公告、记录已读 | 无，由本系统内维护 | ✅ |

> 说明：
> - ✅ 已完成，❌ 未完成。
> - 采购端/供应商端/外部系统责任分工完全同步自 prd.json/PRD.md。
> - 公告栏 US-501 属于通用运营能力，不参与主链依赖。
|------|------|------|
| 前端框架 | React + TypeScript | 18 / 5.3 |
| UI 组件库 | Ant Design | 5.x |
| 构建工具 | Vite | 5.x |
| 状态管理 | Zustand | 4.x |
| HTTP 客户端 | Axios | 1.6.x |
| 后端框架 | FastAPI (Python 3.12) | 0.109 |
| ORM | SQLAlchemy 2.0 (async) | 2.0.25 |
| 数据库 | SQLite (aiosqlite) | - |

## 项目结构

```
/workspace/projects/
├── .coze                          # 项目配置（构建/运行）
├── backend/                       # Python FastAPI 后端
│   ├── app/
│   │   ├── main.py                # FastAPI 应用入口
│   │   ├── config.py              # 配置管理（Pydantic Settings）
│   │   ├── database.py            # 数据库连接（旧版，未使用）
│   │   ├── core/
│   │   │   └── database.py        # 数据库连接（实际使用）
│   │   ├── api/                   # API 路由层
│   │   │   ├── dashboard.py       # 仪表盘接口
│   │   │   ├── suppliers.py       # 供应商管理
│   │   │   ├── materials.py       # 物料/原料管理
│   │   │   ├── products.py        # 产品管理
│   │   │   ├── purchase_orders.py # 采购订单
│   │   │   ├── sales_orders.py    # 销售订单
│   │   │   ├── production.py      # 生产记录
│   │   │   └── warehouses.py      # 仓库管理
│   │   ├── models/                # ORM 模型
│   │   │   ├── supply_chain.py    # 核心业务模型（SQLite 兼容）
│   │   │   ├── supplier.py        # DDD 供应商模型
│   │   │   ├── purchase_order.py  # DDD 采购订单模型
│   │   │   ├── batch.py           # 批次模型
│   │   │   ├── quality_inspection.py # 质检模型
│   │   │   ├── inventory.py       # 库存模型
│   │   │   ├── waybill.py         # 运单模型
│   │   │   ├── pit_cellar.py      # 窖池模型
│   │   │   └── production_order.py # 生产订单模型
│   │   ├── schemas/               # Pydantic Schema
│   │   ├── services/              # 领域服务
│   │   └── routers/               # DDD 风格路由（备用）
│   ├── init_db.py                 # 数据库初始化 & 种子数据
│   └── requirements.txt           # Python 依赖
├── frontend/                      # React 前端
│   ├── src/
│   │   ├── main.tsx               # 入口文件
│   │   ├── App.tsx                # 路由配置
│   │   ├── index.css              # 全局样式
│   │   ├── pages/                 # 页面组件
│   │   │   ├── buyer/             # 采购端页面
│   │   │   │   ├── BuyerHome.tsx  # 采购端首页
│   │   │   │   ├── SourcingList.tsx    # 寻源项目列表
│   │   │   │   ├── SourcingDetail.tsx  # 寻源项目详情
│   │   │   │   └── ContractList.tsx    # 合同管理
│   │   │   ├── supplier/          # 供应商端页面
│   │   │   │   ├── SupplierHome.tsx    # 供应商端首页
│   │   │   │   ├── InvitationList.tsx # 收到的邀请
│   │   │   │   ├── BidList.tsx        # 投标管理
│   │   │   │   ├── ContractList.tsx    # 合同管理
│   │   │   │   └── OrderList.tsx      # 销售订单
│   │   │   ├── PurchaseOrderList.tsx    # 采购订单列表
│   │   │   ├── PurchaseOrderDetail.tsx # 采购订单详情
│   │   │   ├── SupplierList.tsx   # 供应商列表
│   │   │   ├── ReceiptList.tsx    # 入库单列表
│   │   │   ├── InventoryList.tsx  # 库存查询
│   │   │   └── InspectionList.tsx # 质检单列表
│   │   ├── components/
│   │   │   └── Layout.tsx         # 整体布局（侧边栏+内容区）
│   │   ├── api/                   # API 调用层
│   │   │   ├── request.ts         # Axios 实例配置
│   │   │   └── index.ts           # API 函数导出
│   │   ├── store/                 # Zustand 状态管理
│   │   └── types/                 # TypeScript 类型定义
│   ├── vite.config.ts             # Vite 配置（含代理）
│   └── package.json
├── docs/                          # 设计文档
│   ├── PRD.md                     # 产品需求文档
│   ├── DDD-领域设计.md            # DDD 领域设计
│   ├── 技术架构设计.md             # 技术架构
│   ├── E2E测试方案.md             # E2E 测试方案
│   └── ui/                        # UI 原型（HTML）
└── tests/                         # 测试
    ├── api/                       # API 测试（Python pytest）
    └── e2e/                       # E2E 测试（Playwright）
```

## 构建和运行命令

### 开发环境
```bash
# 后端：安装依赖 + 初始化数据库 + 启动服务（端口 8000）
cd backend && pip3 install -r requirements.txt && python3 init_db.py && uvicorn app.main:app --host 0.0.0.0 --port 8000

# 前端：安装依赖 + 启动开发服务器（端口 5000，代理到后端 8000）
cd frontend && pnpm install && npx vite --port 5000 --host 0.0.0.0
```

### 生产环境
```bash
# 前端构建
cd frontend && pnpm build

# 静态文件服务
npx server -l 5000
```

## API 接口清单

### Phase 1: 供应商准入与主数据协同 (US-101~US-108)

| 方法 | 路径 | 功能 | 状态 |
|------|------|------|------|
| GET | `/health` | 健康检查 | ✅ |
| GET | `/suppliers/` | 供应商列表 | ✅ |
| POST | `/suppliers/` | 创建供应商 | ✅ |
| GET | `/suppliers/{id}` | 供应商详情 | ✅ |
| PUT | `/suppliers/{id}` | 更新供应商 | ✅ |
| POST | `/suppliers/{id}/qualifications` | 提交资质文件 | ✅ |
| GET | `/suppliers/{id}/qualifications` | 获取资质列表 | ✅ |
| GET | `/suppliers/qualifications/{qual_id}` | 资质详情 | ✅ |
| POST | `/qualifications/{qual_id}/review` | 资质评审（通过/拒绝） | ✅ |
| GET | `/dashboard/buyer-home` | 采购端首页统计 | ✅ |
| GET | `/dashboard/supplier-home` | 供应商端首页统计 | ✅ |

### Phase 2: 寻源与合同协同 (US-201~US-208)

| 方法 | 路径 | 功能 | 状态 |
|------|------|------|------|
| GET | `/sourcing/` | 寻源项目列表 | ✅ |
| POST | `/sourcing/` | 创建寻源项目 | ✅ |
| GET | `/sourcing/{id}` | 寻源项目详情 | ✅ |
| POST | `/sourcing/{id}/invite` | 邀请供应商 | ✅ |
| GET | `/sourcing/{id}/invitations` | 查看邀请列表 | ✅ |
| POST | `/sourcing/{id}/invitations/{inv_id}/accept` | 供应商接受邀请 | ✅ |
| POST | `/sourcing/{id}/invitations/{inv_id}/decline` | 供应商拒绝邀请 | ✅ |
| GET | `/sourcing/{id}/bids` | 供应商投标列表 | ✅ |
| POST | `/sourcing/{id}/bids` | 供应商投标 | ✅ |
| PUT | `/sourcing/{sourcing_id}/bids/{bid_id}` | 供应商修改投标 | ✅ |
| GET | `/sourcing/{id}/bids/{bid_id}` | 投标详情 | ✅ |
| POST | `/sourcing/{id}/open` | 开标 | ✅ |
| POST | `/sourcing/{sourcing_id}/bids/{bid_id}/award` | 授标 | ✅ |
| GET | `/contracts/` | 合同列表 | ✅ |
| GET | `/contracts/{id}` | 合同详情 | ✅ |
| POST | `/contracts/{id}/sign` | 合同签署 | ✅ |

### Phase 3: 预测与订单执行协同 (US-301~US-315)

| 方法 | 路径 | 功能 | 状态 |
|------|------|------|------|
| GET | `/materials/` | 物料/原料列表 | ✅ |
| GET | `/materials/low-stock` | 低库存物料 | ✅ |
| GET | `/products/` | 产品列表 | ✅ |
| GET | `/products/categories` | 产品分类 | ✅ |
| GET | `/products/brands` | 产品品牌 | ✅ |
| GET | `/purchase-orders/` | 采购订单列表 | ✅ |
| GET | `/purchase-orders/{id}` | 订单详情 | ✅ |
| POST | `/purchase-orders/` | 创建采购订单 | ✅ |
| PUT | `/purchase-orders/{id}` | 更新采购订单 | ✅ |
| POST | `/purchase-orders/{id}/confirm` | 确认采购订单 | ✅ |
| POST | `/purchase-orders/{id}/dispatch` | 发货 | ✅ |
| GET | `/sales-orders/` | 销售订单列表 | ✅ |
| GET | `/production/today-stats` | 今日生产统计 | ✅ |
| GET | `/production/records` | 生产记录列表 | ✅ |
| GET | `/warehouses/` | 仓库列表 | ✅ |
| GET | `/receipts/` | 入库单列表 | ✅ |
| POST | `/receipts/` | 创建入库单 | ✅ |
| GET | `/inspections/` | 质检单列表 | ✅ |
| POST | `/inspections/` | 创建质检单 | ✅ |
| GET | `/inventory/` | 库存查询 | ✅ |
| GET | `/announcements/` | 公告列表 | ✅ |
| POST | `/announcements/` | 发布公告 | ✅ |
| GET | `/announcements/{id}` | 公告详情 | ✅ |
| PUT | `/announcements/{id}` | 编辑公告 | ✅ |
| DELETE | `/announcements/{id}` | 删除公告 | ✅ |
| POST | `/announcements/{id}/record-read` | 记录阅读 | ✅ |
| GET | `/announcements/types/summary` | 类型统计 | ✅ |

### 仪表盘 & 通用

| 方法 | 路径 | 功能 | 状态 |
|------|------|------|------|
| GET | `/dashboard/stats` | 仪表盘核心指标 | ✅ |
| GET | `/dashboard/inventory-alerts` | 库存预警信息 | ✅ |

## 关键技术说明

### 前端代理配置
前端 Vite 开发服务器在 `vite.config.ts` 中配置了 API 代理：
- 所有 `/dashboard`, `/suppliers`, `/materials`, `/products`, `/purchase-orders`, `/sales-orders`, `/production`, `/warehouses` 路径的请求
- 代理到后端 `http://localhost:8000`

### 数据库
- **开发环境**：使用 SQLite（`supply_chain.db`），通过 `aiosqlite` 异步驱动
- **初始化**：执行 `python3 init_db.py` 自动建表并填充 Demo 种子数据
- **模型兼容性**：DDD 模型已从 PostgreSQL 类型（UUID, JSONB）迁移为 SQLite 兼容类型（String(36), Text）

### 双模型体系
项目存在两套模型：
1. **`app/models/supply_chain.py`**：简化版模型，被 API 路由实际使用，基于 `app.core.database.Base`
2. **`app/models/*.py`**：DDD 完整模型，用于领域设计参考，基于 `app.database.Base`

## 常见问题排查

### 后端启动失败
- 检查 Python 依赖：`pip3 install -r backend/requirements.txt`
- 检查数据库初始化：`cd backend && python3 init_db.py`
- 查看日志：`tail -n 50 /app/work/logs/bypass/app.log`

### 前端页面报错
- 检查依赖安装：`cd frontend && pnpm install`
- 确认 `@ant-design/icons` 已安装（多个页面依赖图标组件）
- 查看 Vite 日志：`tail -n 50 /app/work/logs/bypass/console.log`

### API 请求失败
- 确认后端服务运行在 8000 端口
- 确认前端代理配置正确（`vite.config.ts`）
- 直接测试后端：`curl http://localhost:8000/health`

## 项目进度

### 已完成

- **Phase 1 (供应商准入与主数据协同)**：
  - US-101~US-108 全部完成
  - 供应商主数据管理、资质文件上传、资质评审流程
  - 采购端/供应商端首页统计面板

- **Phase 2 (寻源与合同协同)**：
  - US-201~US-209 全部完成
  - 寻源项目创建、供应商邀请、投标管理、开标比价、授标、合同生成与签署
  - 前端重构：去除数据中台，拆分为采购端/供应商端双入口

- **Phase 3 (预测与订单执行协同)**：
  - US-301~US-310 全部完成
  - 采购预测（模拟 ERP 同步）、供应商产能响应、订单确认/拒绝
  - 要货计划、ASN 创建、到货确认、入库单管理、质检

- **Phase 4 (财务结算协同)**：
  - US-401~US-405 全部完成
  - 结算单 CRUD、发票管理、付款流程（申请→审批→付款）
  - 供应商端结算单/发票创建，采购端审批

- **公告栏功能**：
  - 公告、政策、操作指引三种类型
  - 采购端：发布、编辑、删除公告
  - 供应商端：查看公告、记录阅读
  - 支持置顶、优先级、分类筛选

### 待执行

- 无（全部 Phase 已完成）

## 预览与部署链路

### 项目类型判断
- `project_type = "web"`：核心实现围绕浏览器可访问的前端界面（React + Ant Design），通过 Vite 开发服务器提供预览
- 可预览：是

### .coze 配置结构
- 技术项目根目录与工作区根目录重合（`path = "."`），根 `.coze` 同时承担子项目 `.coze` 职责
- `sub_id = "e887fee0"`（不可修改）
- `requires = ["nodejs-24", "python-3.12"]`

### 预览链路（[dev]）
- **build**：`scripts/coze-preview-build.sh` — 安装前端依赖（pnpm）、后端依赖（pip3）、初始化数据库
- **run**：`scripts/coze-preview-run.sh` — 启动后端（uvicorn，端口 8000，后台）+ 启动前端 Vite 开发服务器（端口 5000，前台常驻）
- 前端 Vite 通过 `vite.config.ts` 代理所有 API 路径到后端 8000 端口
- 脚本具备幂等性：每次执行先清理 5000 端口残留进程

### 部署链路（[deploy]）
- `deploy.profile.kind = "service"`, `deploy.profile.flavor = "web"`
- **build**：`scripts/coze-deploy-build.sh` — 安装依赖 + 前端构建（`pnpm run build`）
- **run**：`scripts/coze-deploy-run.sh` — 初始化数据库 + 启动后端（端口 8000，后台）+ 启动 `server.mjs` 静态文件服务（端口 5000，前台）
- `server.mjs` 负责提供前端静态文件并代理 API 请求到后端

### 注意事项
- 后端使用 SQLite，数据库文件 `backend/supply_chain.db`，每次启动前通过 `init_db.py` 初始化
- 前端 Node.js 项目只使用 `pnpm`
- 9000 端口为系统保留，禁止使用





## 安全修复记录

### 2026-07-08: SEC-004 — 从 Git 清除 SAP 连接信息
- 从 Git 跟踪中移除了以下包含 SAP 连接信息的文件：
  - `Integration/probe-latest.json`, `Integration/probe-20260706-225527.json`
  - `Integration/probe-after-unlock.json`, `Integration/probe-2026-07-06.json`
  - `Integration/probe_sap.py`, `Integration/probe-sap-connection.cjs`
  - `Integration/CONNECTION-VERIFICATION.md`, `Integration/CONNECTION-VERIFICATION-FINAL.md`
- 更新 `.gitignore` 防止重新提交
- 脱敏处理 `Integration/README.md`（移除租户 URL 和用户名）
- ⚠️ 如需完全清除 Git 历史中的敏感数据，请执行 `git filter-branch` 或 `BFG Repo-Cleaner`

### 2026-07-08: SEC-001 — 添加 API 认证机制
- 创建 `backend/app/auth.py`：JWT 认证模块
  - 支持 Bearer Token 认证
  - Demo 用户数据库（admin/buyer/supplier1/supplier2）
  - 可选认证模式（未提供 token 时默认 buyer 身份）
  - 角色区分：buyer（采购端）/ supplier（供应商端）
- 创建 `backend/app/api/auth.py`：登录/用户信息 API
  - `POST /auth/login` — 登录获取 token
  - `GET /auth/me` — 获取当前用户信息
  - `GET /auth/demo-mode` — 获取 Demo 可用账号
- 更新 `backend/app/main.py`：注册 auth 路由
- 更新 `backend/app/config.py`：SECRET_KEY 支持环境变量覆盖
- 更新 `backend/requirements.txt`：添加 python-jose 依赖
- 注意：当前为 Demo 级别实现，所有业务路由仍为可选认证模式



