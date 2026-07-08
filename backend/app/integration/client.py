"""Minimal SAP S/4HANA HTTP client for validated read-only endpoints."""

from __future__ import annotations

from dataclasses import dataclass
import httpx

from app.integration.endpoints import SapEndpoint


@dataclass(frozen=True)
class SapClientSettings:
    base_url: str
    sap_client: str
    username: str
    # 密码仅允许来自环境变量 SAP_COMM_PASSWORD，禁止从明文文件读取（SEC-005）
    password: str = ""

    def resolve_password(self) -> str:
        """返回 SAP 密码（必须由环境变量注入）。

        已移除从明文文件（如 user.txt）读取密码的能力：明文凭证文件会被提交到
        Git，造成凭据泄露。密码统一经由环境变量 SAP_COMM_PASSWORD 注入。
        """
        if not self.password:
            raise ValueError(
                "SAP 密码未配置：请通过环境变量 SAP_COMM_PASSWORD 注入，"
                "不要将密码写入明文文件。"
            )
        return self.password


@dataclass(frozen=True)
class SapHttpError(Exception):
    endpoint: SapEndpoint
    status_code: int
    body: str

    def __str__(self) -> str:
        return f"SAP request failed for {self.endpoint.code} with status {self.status_code}"


class SapAuthorizationError(SapHttpError):
    pass


class SapClient:
    def __init__(
        self,
        settings: SapClientSettings,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 30.0,
    ):
        self.settings = settings
        self._transport = transport
        self._timeout = timeout

    def build_url(self, endpoint: SapEndpoint, top: int = 1) -> str:
        params = f"$top={top}&$format=json&sap-client={self.settings.sap_client}"
        return f"{self.settings.base_url.rstrip('/')}{endpoint.path}?{params}"

    def get_json(self, endpoint: SapEndpoint, top: int = 1) -> dict:
        url = self.build_url(endpoint, top=top)
        with httpx.Client(
            auth=(self.settings.username, self.settings.resolve_password()),
            headers={"Accept": "application/json"},
            timeout=self._timeout,
            transport=self._transport,
        ) as client:
            response = client.get(url)

        if response.status_code == 403:
            raise SapAuthorizationError(endpoint, response.status_code, response.text)
        if response.is_error:
            raise SapHttpError(endpoint, response.status_code, response.text)
        return response.json()