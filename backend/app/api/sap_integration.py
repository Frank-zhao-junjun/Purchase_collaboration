"""SAP integration helper APIs for endpoint catalog and read-only probes."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from app.config import settings
from app.integration.client import SapAuthorizationError, SapClient, SapClientSettings, SapHttpError
from app.integration.endpoints import SAP_ENDPOINTS
from app.integration.probe_service import probe_all, save_results, load_results
from app.integration.read_service import SapReadService

router = APIRouter(prefix="/integration/sap", tags=["SAP集成"])


def get_sap_client() -> SapClient:
    sap_settings = SapClientSettings(
        base_url=settings.SAP_BASE_URL,
        sap_client=settings.SAP_CLIENT,
        username=settings.SAP_COMM_USER,
        password=settings.SAP_COMM_PASSWORD,
        credentials_file=settings.SAP_CREDENTIALS_FILE,
    )
    return SapClient(settings=sap_settings)


def get_sap_read_service(client: SapClient = Depends(get_sap_client)) -> SapReadService:
    return SapReadService(client)


@router.get("/endpoints")
async def list_sap_endpoints():
    return [
        {
            "code": endpoint.code,
            "name": endpoint.name,
            "odata_version": endpoint.odata_version,
            "communication_scenario": endpoint.communication_scenario,
            "path": endpoint.path,
        }
        for endpoint in SAP_ENDPOINTS.values()
    ]


@router.get("/probe/{endpoint_code}")
async def probe_sap_endpoint(endpoint_code: str, client: SapClient = Depends(get_sap_client)):
    endpoint = SAP_ENDPOINTS.get(endpoint_code.upper())
    if endpoint is None:
        raise HTTPException(status_code=404, detail="SAP endpoint not found")

    try:
        payload = client.get_json(endpoint)
        sample = payload
        if isinstance(payload, dict) and "d" in payload and isinstance(payload["d"], dict):
            results = payload["d"].get("results")
            if isinstance(results, list) and results:
                sample = results[0]
        elif isinstance(payload, dict) and "value" in payload and isinstance(payload["value"], list) and payload["value"]:
            sample = payload["value"][0]

        return {"code": endpoint.code, "status": 200, "result": "OK", "sample": sample}
    except SapAuthorizationError as exc:
        return JSONResponse(
            status_code=403,
            content={"code": endpoint.code, "status": exc.status_code, "result": "FAIL_403", "body": exc.body},
        )
    except SapHttpError as exc:
        return JSONResponse(
            status_code=502,
            content={"code": endpoint.code, "status": exc.status_code, "result": "FAIL", "body": exc.body},
        )


@router.post("/probe")
async def batch_probe_endpoints(client: SapClient = Depends(get_sap_client)):
    """Probe all SAP endpoints in one call and persist results to disk."""
    results = probe_all(client)
    save_results(
        results,
        file_path=settings.SAP_PROBE_RESULTS_FILE,
        tenant=settings.SAP_BASE_URL,
        client_id=settings.SAP_CLIENT,
        user=settings.SAP_COMM_USER,
    )
    ok = sum(1 for r in results if r["result"] == "OK")
    fail_403 = sum(1 for r in results if r["result"] == "FAIL_403")
    fail_404 = sum(1 for r in results if r["result"] == "FAIL_404")
    other = len(results) - ok - fail_403 - fail_404
    return {
        "summary": {
            "total": len(results),
            "ok": ok,
            "forbidden": fail_403,
            "not_found": fail_404,
            "other": other,
        },
        "results": results,
        "saved_to": settings.SAP_PROBE_RESULTS_FILE,
    }


@router.get("/probe/results")
async def get_probe_results():
    """Return the latest persisted probe results from disk."""
    data = load_results(settings.SAP_PROBE_RESULTS_FILE)
    if data is None:
        raise HTTPException(status_code=404, detail="No probe results found. Run POST /integration/sap/probe first.")
    return data


@router.get("/resources/{resource_name}")
async def list_sap_resource(
    resource_name: str,
    top: int = 50,
    service: SapReadService = Depends(get_sap_read_service),
):
    try:
        items = service.list_resource(resource_name, top=top)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="SAP resource not found") from exc

    return {"resource": resource_name, "count": len(items), "items": items}