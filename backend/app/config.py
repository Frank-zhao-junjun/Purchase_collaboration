"""
Application configuration settings
"""
from functools import lru_cache
import os
import secrets
import warnings

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _resolve_secret_key() -> str:
    """SECRET_KEY 必须来自环境变量，禁止硬编码生产密钥（SEC-005）。

    - 若环境变量 SECRET_KEY 已设置，直接使用（建议在 .env 之外通过真实环境变量注入）。
    - 生产环境（DEBUG=False）未设置则直接启动失败，避免误用默认弱密钥。
    - 开发环境（DEBUG=True）未设置则生成临时随机密钥并告警（重启后失效，仅限本地 demo）。
    """
    env_key = os.environ.get("SECRET_KEY")
    if env_key:
        if env_key in ("supply-chain-demo-secret-key-change-in-production", "changeme", "secret", "dev"):
            warnings.warn("SECRET_KEY 使用了已知弱密钥，请立即更换为强随机值。", stacklevel=2)
        return env_key
    if os.environ.get("DEBUG", "True").lower() in ("false", "0", "no"):
        raise RuntimeError(
            "生产环境必须通过环境变量 SECRET_KEY 提供强随机密钥，已拒绝使用默认/空密钥启动。"
        )
    generated = secrets.token_urlsafe(32)
    warnings.warn(
        "未设置 SECRET_KEY，已为开发模式生成临时随机密钥（重启后失效）。"
        "生产环境请通过环境变量 SECRET_KEY 显式配置"
        "（例如：export SECRET_KEY=$(python -c 'import secrets;print(secrets.token_urlsafe(32))')）。",
        stacklevel=2,
    )
    return generated


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    APP_NAME: str = "白酒供应链数字化管控平台"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    # SQLite数据库
    DATABASE_URL: str = "sqlite+aiosqlite:///./supply_chain.db"
    DATABASE_URL_SYNC: str = "sqlite:///./supply_chain.db"
    # 生产环境必须通过环境变量 SECRET_KEY 注入强随机密钥（禁止硬编码默认值）
    SECRET_KEY: str = Field(default_factory=_resolve_secret_key)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    CORS_ORIGINS: list = ["*"]
    API_V1_PREFIX: str = "/api/v1"
    SAP_BASE_URL: str = ""
    SAP_CLIENT: str = "100"
    SAP_COMM_USER: str = ""
    SAP_COMM_PASSWORD: str = ""
    SAP_PROBE_RESULTS_FILE: str = "Integration/probe-latest.json"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
