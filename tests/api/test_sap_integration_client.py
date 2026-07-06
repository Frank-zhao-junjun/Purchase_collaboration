from pathlib import Path
import sys

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.integration.client import SapAuthorizationError, SapClient, SapClientSettings
from app.integration.endpoints import SAP_ENDPOINTS
from app.integration.probe_service import probe_all, save_results, load_results


def test_loads_password_from_credentials_file(tmp_path: Path):
    credentials_file = tmp_path / "user.txt"
    credentials_file.write_text(
        "Communication User: REDACTED_SAP_COMM_USER\nPassword: P@ss$2$C-Example\n",
        encoding="utf-8",
    )

    settings = SapClientSettings(
        base_url="https://example.sap.com",
        sap_client="100",
        username="REDACTED_SAP_COMM_USER",
        credentials_file=str(credentials_file),
    )

    assert settings.resolve_password() == "P@ss$2$C-Example"


def test_build_url_includes_required_query_parameters():
    client = SapClient(
        settings=SapClientSettings(
            base_url="https://example.sap.com",
            sap_client="100",
            username="REDACTED_SAP_COMM_USER",
            password="secret",
        )
    )

    url = client.build_url(SAP_ENDPOINTS["INT-15"])

    assert url == (
        "https://example.sap.com/sap/opu/odata/sap/API_PRODUCT_SRV/"
        "A_Product?$top=1&$format=json&sap-client=100"
    )


def test_get_json_returns_payload_for_ok_response():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Accept"] == "application/json"
        assert request.url.params["sap-client"] == "100"
        return httpx.Response(200, json={"d": {"results": [{"Product": "4"}]}})

    client = SapClient(
        settings=SapClientSettings(
            base_url="https://example.sap.com",
            sap_client="100",
            username="REDACTED_SAP_COMM_USER",
            password="secret",
        ),
        transport=httpx.MockTransport(handler),
    )

    payload = client.get_json(SAP_ENDPOINTS["INT-15"])

    assert payload["d"]["results"][0]["Product"] == "4"


def test_get_json_raises_authorization_error_for_403_response():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"error": {"message": "Forbidden"}})

    client = SapClient(
        settings=SapClientSettings(
            base_url="https://example.sap.com",
            sap_client="100",
            username="REDACTED_SAP_COMM_USER",
            password="secret",
        ),
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(SapAuthorizationError) as exc_info:
        client.get_json(SAP_ENDPOINTS["INT-08"])

    assert exc_info.value.status_code == 403
    assert exc_info.value.endpoint.code == "INT-08"


# ---------------------------------------------------------------------------
# probe_service tests
# ---------------------------------------------------------------------------


def _mock_client(status_map: dict[str, int], base_url: str = "https://example.sap.com") -> SapClient:
    """Build a SapClient whose MockTransport returns per-endpoint status codes."""

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        for code, path in [
            (ep.code, ep.path) for ep in SAP_ENDPOINTS.values()
        ]:
            if path in url:
                status = status_map.get(code, 200)
                if status == 200:
                    return httpx.Response(200, json={"d": {"results": [{"Product": "4"}]}})
                elif status == 403:
                    return httpx.Response(403, json={"error": {"message": {"value": "Forbidden"}}})
                elif status == 404:
                    return httpx.Response(404, json={"error": {"message": {"value": "Not Found"}}})
        return httpx.Response(200, json={"d": {"results": []}})

    return SapClient(
        settings=SapClientSettings(
            base_url=base_url,
            sap_client="100",
            username="REDACTED_SAP_COMM_USER",
            password="secret",
        ),
        transport=httpx.MockTransport(handler),
    )


def test_probe_all_returns_result_for_every_endpoint():
    client = _mock_client({code: 200 for code in SAP_ENDPOINTS})
    results = probe_all(client)

    assert len(results) == len(SAP_ENDPOINTS)
    for r in results:
        assert r["result"] == "OK"
        assert r["status"] == 200
        assert r["code"] in SAP_ENDPOINTS


def test_probe_all_captures_403_as_fail_without_raising():
    client = _mock_client({"INT-08": 403, **{c: 200 for c in SAP_ENDPOINTS if c != "INT-08"}})
    results = probe_all(client)

    by_code = {r["code"]: r for r in results}
    assert by_code["INT-08"]["result"] == "FAIL_403"
    assert by_code["INT-08"]["status"] == 403
    assert by_code["INT-15"]["result"] == "OK"


def test_save_and_load_results_round_trip(tmp_path: Path):
    client = _mock_client({"INT-05": 403, **{c: 200 for c in SAP_ENDPOINTS if c != "INT-05"}})
    results = probe_all(client)

    output_file = str(tmp_path / "probe-test.json")
    save_results(results, file_path=output_file, tenant="https://example.sap.com", client_id="100", user="REDACTED_SAP_COMM_USER")

    loaded = load_results(output_file)
    assert loaded is not None
    assert loaded["summary"]["total"] == len(SAP_ENDPOINTS)
    assert loaded["summary"]["ok"] == len(SAP_ENDPOINTS) - 1
    assert loaded["summary"]["forbidden"] == 1
    assert len(loaded["results"]) == len(SAP_ENDPOINTS)


def test_load_results_returns_none_for_missing_file(tmp_path: Path):
    assert load_results(str(tmp_path / "nonexistent.json")) is None