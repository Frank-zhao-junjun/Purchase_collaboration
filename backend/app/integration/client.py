"""Minimal SAP S/4HANA HTTP client for validated read-only endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import httpx

from app.integration.endpoints import SapEndpoint


@dataclass(frozen=True)
class SapClientSettings:
    base_url: str
    sap_client: str
    username: str
    password: str = ""
    credentials_file: str = ""

    def resolve_password(self) -> str:
        if self.password:
            return self.password
        if not self.credentials_file:
            raise ValueError("SAP password is not configured")

        file_text = Path(self.credentials_file).read_text(encoding="utf-8")
        for line in file_text.splitlines():
            # 支持半角冒号 ":" 和全角冒号 "："
            sep_pos = -1
            for sep in (":", "："):
                pos = line.find(sep)
                if pos != -1:
                    sep_pos = pos
                    break
            if sep_pos == -1:
                continue
            key, value = line[:sep_pos], line[sep_pos + 1:]
            if key.strip().lower() == "password":
                password = value.strip()
                if password:
                    return password
        raise ValueError(f"Password not found in credentials file: {self.credentials_file}")


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