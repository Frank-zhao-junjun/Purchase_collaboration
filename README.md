# 白酒供应链数字化管控平台

面向白酒企业的供应链全链路数字化管控系统 Demo，聚焦"采购→到货验收→入库→库存管理"核心链路。

## 系统功能

### 供应商准入与主数据协同 (Phase 1)
- 供应商注册邀请与自助注册
- 供应商资格评审项目管理
- 资质文件上传与评审流程
- 资质过期预警与重认证

### 寻源与合同协同 (Phase 2)
- 寻源项目发布（RFQ/RFP/RFI）
- 供应商邀请与投标管理
- 开标比价与授标
- 合同草案生成与在线签署

### 预测与订单执行协同 (Phase 3)
- 采购预测发布与产能响应
- 采购订单发布与确认
- 要货计划确认与调整
- ASN 创建与送货计划管理
- 收货验收与入库

### 财务结算协同 (Phase 4)
- 结算单创建与审核
- 发票管理与三单匹配
- 付款申请与审批

### 公告栏运营
- 公告、政策、操作指引发布
- 已读记录管理

## 技术架构

### 后端
- **框架**: FastAPI + SQLAlchemy 2.0 (async)
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **API文档**: Swagger UI (/docs)

### 前端
- **框架**: React 18 + TypeScript
- **UI库**: Ant Design 5.x
- **状态管理**: Zustand
- **构建工具**: Vite

## 快速启动

### 开发环境

```bash
# 后端：安装依赖 + 初始化数据库 + 启动服务（端口 8000）
cd backend && pip3 install -r requirements.txt && python3 init_db.py && uvicorn app.main:app --host 0.0.0.0 --port 8000

# 前端：安装依赖 + 启动开发服务器（端口 5000）
cd frontend && pnpm install && npx vite --port 5000 --host 0.0.0.0
```

### 生产环境

```bash
# 构建
pnpm build

# 启动服务（前端静态服务器 + API 代理）
node server.mjs
```

### Docker 一键启动（推荐验收）

```bash
# 在仓库根目录执行
docker compose up -d --build

# 可选：查看服务状态
docker compose ps
```

服务就绪后访问：
- 前端（Nginx）：`http://localhost:3000`
- 后端 API 文档：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/health`

停止并清理：

```bash
docker compose down
```

如需全新数据重测（删除卷）：

```bash
docker compose down -v
```

## 3 步最短验收流程（复制即跑）

```bash
# 1) 启动整套服务
docker compose up -d --build

# 2) 跑全量 US 测试（择一）
./scripts/run-us-tests.sh --nginx
# 或 PowerShell:
# .\scripts\run-us-tests.ps1 -ThroughNginx

# 3) 验收完成后清理
docker compose down
```

## 全量 US 测试结果 (2026-07-05)

| Phase | US 范围 | 测试结果 | 测试覆盖 |
|-------|---------|----------|----------|
| **Phase 1** | US-101~US-109 | ✅ 全部通过 | 邀请创建/验证、注册提交/审核、资格评审、资质预警/重认证 |
| **Phase 2** | US-201~US-208 | ✅ 全部通过 | 寻源项目、邀请接受/拒绝、投标、授标、合同签署/评论 |
| **Phase 3** | US-301~US-310 | ✅ 全部通过 | 预测、订单确认、要货计划、ASN创建/提交、入库/发货 |
| **Phase 4** | US-401~US-405 | ✅ 全部通过 | 结算单创建/确认、发票创建、付款创建/审批/确认 |
| **US-501** | 公告栏 | ✅ 全部通过 | 公告 CRUD + 已读 + 类型统计 |

## 访问地址

| 服务 | 地址 |
|------|------|
| 前端界面 | http://localhost:5000 |
| API文档 | http://localhost:8000/docs |
| 健康检查 | http://localhost:8000/health |

## 项目结构

```
supply-chain-demo/
├── .coze                    # Coze 项目配置
├── .cozeproj               # Coze 脚手架脚本
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── api/            # API 路由层
│   │   ├── core/           # 核心配置
│   │   ├── models/         # ORM 模型
│   │   └── schemas/        # Pydantic Schema
│   ├── init_db.py          # 数据库初始化
│   └── requirements.txt    # Python 依赖
├── frontend/               # React 前端
│   ├── src/
│   │   ├── pages/         # 页面组件
│   │   │   ├── buyer/     # 采购端页面
│   │   │   └── supplier/ # 供应商端页面
│   │   ├── components/    # 公共组件
│   │   ├── api/           # API 调用
│   │   └── store/         # Zustand 状态
│   └── package.json
├── docs/                   # 设计文档
│   ├── PRD.md             # 产品需求文档
│   └── DDD-领域设计.md    # DDD 领域设计
├── tests/                  # 测试
│   └── api/               # API 测试
├── scripts/                # 脚本
│   └── run-us-tests.*     # 全量 US 测试脚本
└── server.mjs             # 生产环境静态服务器
```

## API 接口清单

### 供应商准入 (Phase 1)

| 方法 | 路径 | 功能 | US |
|------|------|------|-----|
| POST | `/supplier-portal/invitations` | 创建注册邀请 | US-101-1 |
| GET | `/supplier-portal/invitations` | 获取邀请列表 | US-101-2 |
| GET | `/supplier-portal/invitations/{code}/validate` | 验证邀请码 | US-101-2 |
| POST | `/supplier-portal/register` | 供应商自助注册 | US-102-1 |
| GET | `/supplier-portal/register/status` | 查询注册状态 | US-102-2 |
| GET | `/supplier-portal/pending-audit` | 待审核注册列表 | US-103-2 |
| GET | `/supplier-portal/registrations/{id}` | 注册详情 | US-103-2 |
| POST | `/supplier-portal/registrations/{id}/audit` | 审核注册申请 | US-103-1 |
| POST | `/supplier-portal/registrations/{id}/resubmit` | 重新提交 | US-103-2 |
| GET | `/qualification/projects` | 资格评审项目列表 | US-104-2 |
| POST | `/qualification/projects` | 创建资格评审项目 | US-104-1 |
| GET | `/qualification/projects/{id}` | 评审项目详情 | US-105-2 |
| GET | `/qualification/projects/{id}/questionnaire` | 获取评审问卷 | US-105-1 |
| POST | `/qualification/projects/{id}/submission` | 提交资格问卷 | US-105-1 |
| GET | `/qualification/projects/{id}/submissions` | 查看提交列表 | US-105-2 |
| POST | `/qualification/projects/{id}/submissions/{sid}/review` | 评审资格文件 | US-106-1 |
| POST | `/qualification/projects/{id}/approve` | 批准资格 | US-107-1 |
| POST | `/qualification/projects/{id}/reject` | 拒绝资格 | US-107-1 |
| GET | `/supplier-portal/supplier-alerts` | 资质预警列表 | US-108-2 |
| POST | `/supplier-portal/cert-alerts/check` | 触发资质检查 | US-108-1 |
| POST | `/supplier-portal/supplier-alerts/{id}/resolve` | 处理预警 | US-108-2 |
| GET | `/supplier-portal/suppliers/{id}/certifications` | 供应商资质列表 | US-109-2 |
| POST | `/supplier-portal/suppliers/{id}/certifications` | 新增资质 | US-109-1 |

### 寻源与合同 (Phase 2)

| 方法 | 路径 | 功能 | US |
|------|------|------|-----|
| GET | `/sourcing/projects` | 寻源项目列表 | US-201-2 |
| POST | `/sourcing/projects` | 创建寻源项目 | US-201-1 |
| GET | `/sourcing/projects/{id}` | 寻源项目详情 | US-201-2 |
| GET | `/sourcing/projects/invitations` | 供应商收到的邀请 | US-202-1 |
| POST | `/sourcing/projects/{id}/accept` | 接受邀请 | US-202-1 |
| POST | `/sourcing/projects/{id}/decline` | 拒绝邀请 | US-202-1 |
| GET | `/sourcing/projects/{id}/bid` | 获取投标表单 | US-203-1 |
| POST | `/sourcing/projects/{id}/bid` | 提交投标 | US-203-1 |
| POST | `/sourcing/projects/{id}/open-bids` | 开标 | US-203-1 |
| GET | `/sourcing/projects/{id}/comparison` | 比价表 | US-204-1 |
| POST | `/sourcing/projects/{id}/award` | 授标 | US-205-1 |
| GET | `/contracts/` | 合同列表 | US-206-2 |
| GET | `/contracts/{id}` | 合同详情 | US-206-2 |
| POST | `/contracts/{id}/comments` | 添加合同评论 | US-207-1 |
| GET | `/contracts/drafts/{id}` | 合同草案 | US-206-2 |
| POST | `/contracts/{id}/sign-initiate` | 发起签署 | US-208-1 |
| POST | `/contracts/{id}/sign` | 签署合同 | US-208-2 |
| GET | `/contracts/{id}/sign-status` | 签署状态 | US-209-1/2 |

### 预测与订单执行 (Phase 3)

| 方法 | 路径 | 功能 | US |
|------|------|------|-----|
| GET | `/supplier-portal/forecasts` | 采购预测列表 | US-301-2 |
| GET | `/supplier-portal/forecasts/{id}` | 预测详情 | US-301-2 |
| POST | `/supplier-portal/forecasts/{id}/respond` | 产能响应 | US-302-1 |
| GET | `/purchase-orders/` | 采购订单列表 | US-303-1 |
| GET | `/supplier-portal/orders` | 供应商订单列表 | US-303-2 |
| POST | `/supplier-portal/orders/{id}/confirm` | 确认/拒绝订单 | US-303-2 |
| GET | `/supplier-portal/delivery-schedules` | 要货计划列表 | US-305-2 |
| POST | `/supplier-portal/delivery-schedules/{id}/confirm` | 确认要货计划 | US-306-1 |
| GET | `/supplier-portal/asns` | ASN 列表 | US-307-2 |
| POST | `/supplier-portal/asns` | 创建 ASN | US-307-1 |
| POST | `/supplier-portal/asns/{id}/submit` | 提交 ASN | US-307-1 |
| GET | `/logistics/shipment-notes/` | 发货单列表 | US-308-2 |
| POST | `/logistics/shipment-notes/{id}/arrive` | 到货确认 | US-310-1 |
| GET | `/logistics/receipts/` | 入库单列表 | US-310-2 |
| POST | `/logistics/receipts/` | 创建入库单 | US-310-1 |

### 财务结算 (Phase 4)

| 方法 | 路径 | 功能 | US |
|------|------|------|-----|
| GET | `/financial/statements/` | 结算单列表 | US-401-2 |
| POST | `/financial/statements/` | 创建结算单 | US-401-1 |
| GET | `/financial/statements/{id}` | 结算单详情 | US-401-2 |
| POST | `/financial/statements/{id}/confirm` | 确认结算单 | US-401-2 |
| GET | `/financial/invoices/` | 发票列表 | US-403-2 |
| POST | `/financial/invoices/` | 创建发票 | US-403-1 |
| GET | `/financial/invoices/{id}` | 发票详情 | US-403-2 |
| GET | `/financial/payments/` | 付款记录列表 | US-405-2 |
| POST | `/financial/payments/` | 创建付款申请 | US-405-1 |
| POST | `/financial/payments/{id}/approve` | 审批付款 | US-405-1 |
| POST | `/financial/payments/{id}/pay` | 确认付款 | US-405-1 |

### 公告栏

| 方法 | 路径 | 功能 | US |
|------|------|------|-----|
| GET | `/announcements/` | 公告列表 | US-501-2 |
| POST | `/announcements/` | 发布公告 | US-501-1 |
| GET | `/announcements/{id}` | 公告详情 | US-501-2 |
| PUT | `/announcements/{id}` | 编辑公告 | US-501-1 |
| DELETE | `/announcements/{id}` | 删除公告 | US-501-1 |
| POST | `/announcements/{id}/record-read` | 记录已读 | US-501-2 |
| GET | `/announcements/types/summary` | 类型统计 | US-501-2 |

### 仪表盘与通用

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/dashboard/stats` | 仪表盘统计 |
| GET | `/suppliers/` | 供应商列表 |
| GET | `/suppliers/{id}` | 供应商详情 |
| GET | `/materials/` | 物料列表 |
| GET | `/products/` | 产品列表 |
| GET | `/warehouses/` | 仓库列表 |

## 许可证

MIT License
