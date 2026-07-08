"""JWT 认证模块 - 为 Demo 提供基本的 API 认证和授权"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from app.config import settings

# 使用 HTTP Bearer token 方案
security = HTTPBearer(auto_error=False)


class TokenData(BaseModel):
    """Token 中包含的用户信息"""
    user_id: int
    username: str
    role: str  # "buyer" 或 "supplier"
    supplier_id: Optional[int] = None


class UserCredentials(BaseModel):
    """Demo 用户凭据"""
    username: str
    password: str


# Demo 用户数据库（模拟，实际应使用数据库存储）
DEMO_USERS = {
    "admin": {
        "user_id": 1,
        "username": "admin",
        "password": "admin123",
        "role": "buyer",
        "supplier_id": None,
    },
    "buyer": {
        "user_id": 2,
        "username": "buyer",
        "password": "buyer123",
        "role": "buyer",
        "supplier_id": None,
    },
    "supplier1": {
        "user_id": 3,
        "username": "supplier1",
        "password": "supplier123",
        "role": "supplier",
        "supplier_id": 1,
    },
    "supplier2": {
        "user_id": 4,
        "username": "supplier2",
        "password": "supplier123",
        "role": "supplier",
        "supplier_id": 2,
    },
}


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建 JWT access token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str) -> Optional[TokenData]:
    """验证 JWT token 并返回用户信息"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("user_id")
        username: str = payload.get("username")
        role: str = payload.get("role")
        supplier_id: Optional[int] = payload.get("supplier_id")

        if username is None or role is None:
            return None

        return TokenData(
            user_id=user_id,
            username=username,
            role=role,
            supplier_id=supplier_id,
        )
    except JWTError:
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[TokenData]:
    """获取当前用户（可选认证 - 不强制要求 token）"""
    if credentials is None:
        # Demo 模式：未提供 token 时返回默认采购员身份
        return TokenData(user_id=2, username="buyer", role="buyer", supplier_id=None)
    
    token_data = verify_token(credentials.credentials)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data


async def get_current_user_required(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenData:
    """获取当前用户（强制要求 token）"""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要认证",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_data = verify_token(credentials.credentials)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data


def require_role(required_role: str):
    """依赖注入工厂：要求特定角色"""
    async def role_checker(current_user: TokenData = Depends(get_current_user_required)):
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要 {required_role} 角色权限",
            )
        return current_user
    return role_checker
