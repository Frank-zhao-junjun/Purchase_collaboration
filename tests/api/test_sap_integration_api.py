from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.api.sap_integration import get_sap_client, get_sap_read_service, router
from app.integration.client import SapAuthorizationError
from app.integration.endpoints import SAP_ENDPOINTS


class FakeSapClient:
    def __init__(self, payload=None, error=None):
        self.payload = payload or {"d": {"results": []}}
        self.error = error

    def get_json(self, endpoint, top=1):
        if self.error:
            raise self.error
        return self.payload


def create_test_client(fake_client: FakeSapClient) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_sap_client] = lambda: fake_client
    return TestClient(app)


def create_test_client_with_service(fake_service) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_sap_read_service] = lambda: fake_service
    return TestClient(app)


def test_list_sap_endpoints_returns_catalog():
    client = create_test_client(FakeSapClient())

    response = client.get("/integration/sap/endpoints")

    assert response.status_code == 200
    body = response.json()
    assert len(body) >= 8
    assert body[0]["code"].startswith("INT-")
    assert any(row["code"] == "INT-15" for row in body)


def test_probe_endpoint_returns_forbidden_status_from_sap_client():
    client = create_test_client(
        FakeSapClient(
            error=SapAuthorizationError(
                endpoint=SAP_ENDPOINTS["INT-08"],
                status_code=403,
                body='{"error": "Forbidden"}',
            )
        )
    )

    response = client.get("/integration/sap/probe/INT-08")

    assert response.status_code == 403
    assert response.json()["code"] == "INT-08"
    assert response.json()["status"] == 403


def test_read_materials_resource_returns_normalized_items():
    class FakeReadService:
        def list_resource(self, resource_name, top=50):
            assert resource_name == "materials"
            assert top == 50
            return [{"sap_material_code": "MAT-001", "name": "MAT-001"}]

    client = create_test_client_with_service(FakeReadService())

    response = client.get("/integration/sap/resources/materials")

    assert response.status_code == 200
    assert response.json() == {
        "resource": "materials",
        "count": 1,
        "items": [{"sap_material_code": "MAT-001", "name": "MAT-001"}],
    }