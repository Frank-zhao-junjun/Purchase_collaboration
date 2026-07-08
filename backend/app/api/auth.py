"""认证 API 路由 - 登录/登出/用户信息"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer

from app.auth import (
    DEMO_USERS,
    TokenData,
    create_access_token,
    get_current_user,
    get_current_user_required,
)

router = APIRouter(prefix="/auth", tags=["认证管理"])


@router.post("/login")
async def login(payload: UserCredentials):
    """用户登录，返回 JWT token（接受 JSON 请求体）"""
    user = DEMO_USERS.get(payload.username)
    if not user or user["password"] != payload.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    token = create_access_token(
        data={
            "user_id": user["user_id"],
            "username": user["username"],
            "role": user["role"],
            "supplier_id": user["supplier_id"],
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "user_id": user["user_id"],
            "username": user["username"],
            "role": user["role"],
            "supplier_id": user["supplier_id"],
        },
    }


@router.get("/me")
async def get_me(current_user: TokenData = Depends(get_current_user_required)):
    """获取当前登录用户信息"""
    return {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "role": current_user.role,
        "supplier_id": current_user.supplier_id,
    }


@router.get("/demo-mode")
async def get_demo_mode():
    """获取 Demo 模式的默认用户信息和可用账号（不含密码）"""
    return {
        "demo_mode": True,
        "default_user": {
            "user_id": 2,
            "username": "buyer",
            "role": "buyer",
        },
        "available_accounts": [
            {"username": "admin", "role": "buyer"},
            {"username": "buyer", "role": "buyer"},
            {"username": "supplier1", "role": "supplier", "supplier_id": 1},
            {"username": "supplier2", "role": "supplier", "supplier_id": 2},
        ],
    }
