"""
Application configuration settings
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "白酒供应链数字化管控平台"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    # SQLite数据库
    DATABASE_URL: str = "sqlite+aiosqlite:///./supply_chain.db"
    DATABASE_URL_SYNC: str = "sqlite:///./supply_chain.db"
    SECRET_KEY: str = "supply-chain-demo-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    CORS_ORIGINS: list = ["*"]
    API_V1_PREFIX: str = "/api/v1"
    SAP_BASE_URL: str = ""
    SAP_CLIENT: str = "100"
    SAP_COMM_USER: str = ""
    SAP_COMM_PASSWORD: str = ""
    SAP_CREDENTIALS_FILE: str = ""
    SAP_PROBE_RESULTS_FILE: str = "Integration/probe-latest.json"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
