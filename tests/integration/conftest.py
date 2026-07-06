"""
集成测试配置 — 真实 SAP S/4HANA 连接测试

标记 @pytest.mark.sap 的测试会连接真实 SAP 租户，需要：
1. Integration/user.txt 含 REDACTED_SAP_COMM_USER 密码（gitignore，不提交）
2. 网络可达 REDACTED-SAP-TENANT.example.com
3. backend/.env 配置 SAP_BASE_URL 等

运行方式：
    # 仅跑 SAP 集成测试
    pytest tests/integration/ -v -m sap

    # 跳过 SAP 集成测试（无凭证/无网络时）
    pytest tests/integration/ -v -m "not sap"

    # 全量（含 SAP 集成测试）
    pytest tests/integration/ -v
"""
import os
import sys
from pathlib import Path

import pytest

# 确保 backend 包可导入
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# 设置工作目录为 backend（使 .env 和相对路径生效）
os.chdir(BACKEND_DIR)


def _credentials_available() -> bool:
    """检查 SAP 凭证是否可用（user.txt 存在且含密码）。"""
    cred_file = PROJECT_ROOT / "Integration" / "user.txt"
    if not cred_file.exists():
        return False
    text = cred_file.read_text(encoding="utf-8")
    for line in text.splitlines():
        sep_pos = -1
        for sep in (":", "："):
            pos = line.find(sep)
            if pos != -1:
                sep_pos = pos
                break
        if sep_pos == -1:
            continue
        key, value = line[:sep_pos], line[sep_pos + 1:]
        if key.strip().lower() == "password" and value.strip():
            return True
    return False


SAP_AVAILABLE = _credentials_available()


def pytest_collection_modifyitems(config, items):
    """无凭证时自动跳过 @pytest.mark.sap 测试。"""
    if not SAP_AVAILABLE:
        skip_sap = pytest.mark.skip(reason="SAP 凭证不可用（Integration/user.txt 无密码）")
        for item in items:
            if "sap" in item.keywords:
                item.add_marker(skip_sap)


@pytest.fixture(scope="session")
def sap_client():
    """提供配置好的 SapClient（真实 SAP 连接）。"""
    from app.config import settings
    from app.integration.client import SapClient, SapClientSettings

    cred_file = str(PROJECT_ROOT / "Integration" / "user.txt")
    sap_settings = SapClientSettings(
        base_url=settings.SAP_BASE_URL,
        sap_client=settings.SAP_CLIENT,
        username=settings.SAP_COMM_USER,
        password=settings.SAP_COMM_PASSWORD,
        credentials_file=cred_file,
    )
    return SapClient(settings=sap_settings)


@pytest.fixture(scope="session")
def project_root():
    return PROJECT_ROOT