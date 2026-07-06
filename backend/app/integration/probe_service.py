"""Batch probe service: probe all SAP endpoints and persist results to disk."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.integration.client import SapAuthorizationError, SapClient, SapHttpError
from app.integration.endpoints import SAP_ENDPOINTS, SapEndpoint


def _probe_one(client: SapClient, endpoint: SapEndpoint) -> dict[str, Any]:
    """Probe a single endpoint. Returns a result dict, never raises."""
    try:
        payload = client.get_json(endpoint)

        # Extract a sample record from the response
        sample: Any = None
        if isinstance(payload, dict):
            if "d" in payload and isinstance(payload["d"], dict):
                results = payload["d"].get("results")
                if isinstance(results, list) and results:
                    sample = results[0]
            elif "value" in payload and isinstance(payload["value"], list) and payload["value"]:
                sample = payload["value"][0]

        return {
            "code": endpoint.code,
            "name": endpoint.name,
            "odata_version": endpoint.odata_version,
            "communication_scenario": endpoint.communication_scenario,
            "path": endpoint.path,
            "status": 200,
            "result": "OK",
            "sample_fields": list(sample.keys()) if isinstance(sample, dict) else [],
        }
    except SapAuthorizationError as exc:
        return {
            "code": endpoint.code,
            "name": endpoint.name,
            "odata_version": endpoint.odata_version,
            "communication_scenario": endpoint.communication_scenario,
            "path": endpoint.path,
            "status": exc.status_code,
            "result": "FAIL_403",
            "error": exc.body[:500] if exc.body else "",
        }
    except SapHttpError as exc:
        return {
            "code": endpoint.code,
            "name": endpoint.name,
            "odata_version": endpoint.odata_version,
            "communication_scenario": endpoint.communication_scenario,
            "path": endpoint.path,
            "status": exc.status_code,
            "result": "FAIL",
            "error": exc.body[:500] if exc.body else "",
        }
    except Exception as exc:
        return {
            "code": endpoint.code,
            "name": endpoint.name,
            "odata_version": endpoint.odata_version,
            "communication_scenario": endpoint.communication_scenario,
            "path": endpoint.path,
            "status": 0,
            "result": "ERROR",
            "error": str(exc)[:500],
        }


def probe_all(client: SapClient) -> list[dict[str, Any]]:
    """Probe every endpoint in SAP_ENDPOINTS. Returns a list of result dicts."""
    results: list[dict[str, Any]] = []
    for endpoint in SAP_ENDPOINTS.values():
        results.append(_probe_one(client, endpoint))
    return results


def save_results(
    results: list[dict[str, Any]],
    file_path: str,
    tenant: str = "",
    client_id: str = "",
    user: str = "",
) -> None:
    """Persist probe results to a JSON file in the unified snapshot format."""
    ok = sum(1 for r in results if r["result"] == "OK")
    fail_403 = sum(1 for r in results if r["result"] == "FAIL_403")
    fail_404 = sum(1 for r in results if r["result"] == "FAIL_404")
    other = len(results) - ok - fail_403 - fail_404

    snapshot = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tenant": tenant,
        "client": client_id,
        "user": user,
        "description": "Batch probe via /integration/sap/probe API",
        "results": results,
        "summary": {
            "total": len(results),
            "ok": ok,
            "forbidden": fail_403,
            "not_found": fail_404,
            "other": other,
        },
    }

    out = Path(file_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")


def load_results(file_path: str) -> dict[str, Any] | None:
    """Load the latest probe results from disk. Returns None if file doesn't exist."""
    p = Path(file_path)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))
