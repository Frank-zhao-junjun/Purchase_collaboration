"""采购供应链协同管理系统 - FastAPI主应用"""
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import suppliers, materials, products, purchase_orders, sales_orders, production, warehouses, dashboard, supplier_portal, supplier_qualification, qualification, sourcing, announcements, logistics, financial, supplier_collaboration, collaboration, sap_integration, auth
from app.auth import get_current_user_required
from app.config import settings

app = FastAPI(title="采购供应链协同管理系统", description="采购供应链协同全流程管理API", version="1.0.0", docs_url="/docs", redoc_url="/redoc")

# CORS：Bearer Token 本身即凭证，无需浏览器 credentials，故关闭
# 生产环境请将 settings.CORS_ORIGINS 限制为受信前端域名
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 认证路由（公开，供前端登录获取 token）
app.include_router(auth.router)

# 业务路由：统一强制 JWT 认证（SEC-001 修复）
# 任意未携带有效 Bearer Token 的请求将被拒绝（401 Unauthorized）
_BUSINESS_ROUTERS = [
    suppliers, materials, products, purchase_orders, sales_orders,
    production, warehouses, dashboard, supplier_portal, supplier_qualification,
    qualification, sourcing, announcements, logistics, financial,
    supplier_collaboration, collaboration, sap_integration,
]
for _mod in _BUSINESS_ROUTERS:
    app.include_router(_mod.router, dependencies=[Depends(get_current_user_required)])

@app.get("/", tags=["首页"])
async def root():
    return {"name": "采购供应链协同管理系统", "version": "1.0.0", "docs": "/docs"}

@app.get("/health", tags=["健康检查"])
async def health_check():
    return {"status": "healthy"}
