"""SAP integration package."""

from app.integration.client import SapAuthorizationError, SapClient, SapClientSettings
from app.integration.endpoints import SAP_ENDPOINTS, SapEndpoint

# Keep package import light; model/probe/read modules can pull runtime dependencies.
try:
    from app.integration.models import SyncLog, SyncQueue, ScenarioConfig, FieldMapping, IdempotencyRecord
except Exception:  # pragma: no cover - optional at import time
    SyncLog = SyncQueue = ScenarioConfig = FieldMapping = IdempotencyRecord = None

try:
    from app.integration.probe_service import probe_all, save_results, load_results
except Exception:  # pragma: no cover - optional at import time
    probe_all = save_results = load_results = None

try:
    from app.integration.read_service import SapReadService
except Exception:  # pragma: no cover - optional at import time
    SapReadService = None

__all__ = [
    "SAP_ENDPOINTS",
    "SapAuthorizationError",
    "SapClient",
    "SapClientSettings",
    "SapEndpoint",
    "SapReadService",
    "SyncLog", "SyncQueue", "ScenarioConfig", "FieldMapping", "IdempotencyRecord",
    "probe_all",
    "save_results",
    "load_results",
]