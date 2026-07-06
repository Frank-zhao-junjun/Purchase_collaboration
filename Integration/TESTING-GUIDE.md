# SAP S/4HANA Cloud 集成测试指南

| 项目 | 值 |
|------|-----|
| 文档版本 | V1.0 |
| 创建日期 | 2026-07-06 |
| 目标系统 | SAP S/4HANA Cloud Public Edition (`REDACTED-SAP-TENANT.example.com`) |
| 关联文档 | `URS-SAP-S4HANA-Integration.md` V0.3, `SAP-API-Verification-Report.md` V2.0 |

---

## 测试金字塔

```
                    ┌─────────────────┐
                    │  L4 端到端测试   │  ← 真实租户 + 全链路
                    ├─────────────────┤
                    │  L3 集成测试     │  ← 真实租户 + 单场景
                    ├─────────────────┤
                    │  L2 契约测试     │  ← Mock Server + OData 元数据
                    ├─────────────────┤
                    │  L1 单元测试     │  ← 纯代码 Mock，无网络
                    └─────────────────┘
```

---

## L1 — 单元测试（无网络依赖）

### 目标

验证适配器（Adapter）的字段映射、数据转换、错误处理逻辑，不依赖任何 SAP 系统。

### 前提

- `backend/app/integration/` 模块已实现
- pytest 已配置（`pytest.ini` 已存在）

### 实现方式

使用 `unittest.mock.MagicMock` 模拟 OData 连接器的响应：

```python
# backend/tests/integration/test_adapters/test_planned_order_adapter.py
import pytest
from unittest.mock import AsyncMock, patch
from app.integration.adapter.planned_order_adapter import PlannedOrderAdapter


@pytest.fixture
def mock_odata_response():
    return {
        "d": {
            "results": [
                {
                    "PlannedOrder": "0010000001",
                    "PlannedOrderType": "PE",
                    "Material": "FG-001",
                    "Plant": "1000",
                    "PlannedQuantity": "1000",
                    "BaseUnit": "EA",
                    "PlannedOrderOpeningDate": "/Date(1782336000000)/",
                }
            ]
        }
    }


class TestPlannedOrderAdapter:
    @pytest.mark.asyncio
    async def test_map_sap_to_platform(self, mock_odata_response):
        """测试 SAP 字段 → 平台字段映射"""
        adapter = PlannedOrderAdapter()
        result = await adapter.map_sap_to_platform(mock_odata_response["d"]["results"][0])

        assert result["sap_planned_order_number"] == "0010000001"
        assert result["material_code"] == "FG-001"
        assert result["plant"] == "1000"
        assert result["quantity"] == 1000.0
        assert result["unit"] == "EA"

    @pytest.mark.asyncio
    async def test_handle_empty_response(self):
        """测试空响应处理"""
        adapter = PlannedOrderAdapter()
        result = await adapter.map_sap_to_platform({})
        assert result is None or result == {}

    @pytest.mark.asyncio
    async def test_handle_sap_date_format(self):
        """测试 SAP /Date(timestamp)/ 格式转换"""
        adapter = PlannedOrderAdapter()
        result = adapter._parse_sap_date("/Date(1782336000000)/")
        assert result is not None
        assert result.year == 2026
```

### 关键测试点

| 测试项 | 说明 |
|--------|------|
| 字段映射正确性 | 每个 Adapter 的 `map_sap_to_platform()` 和 `map_platform_to_sap()` |
| SAP 日期格式 | `/Date(timestamp)/` → Python datetime |
| SAP 数值格式 | 字符串 "1000.000" → float 1000.0 |
| 空值/缺失字段 | SAP 返回 `null` 或字段缺失时的容错 |
| 幂等键生成 | 同一 PO 号多次调用生成相同幂等键 |
| 分页处理 | `$skip` / `$top` 的 next link 解析 |

---

## L2 — 契约测试（Mock OData Server）

### 目标

验证 OData 连接器的请求构造、URL 签名、认证头、响应解析符合 SAP OData 协议规范。

### 实现方式

使用 `responses` 或 `respx` 库拦截 HTTP 请求，返回预设的 OData JSON：

```python
# backend/tests/integration/test_connector/test_odata_v2_connector.py
import pytest
import respx
import httpx
from app.integration.connector.odata_connector import ODataV2Connector


@pytest.fixture
def connector():
    return ODataV2Connector(
        base_url="https://REDACTED-SAP-TENANT.example.com",
        client="100",
        auth=("REDACTED_SAP_COMM_USER", "secret"),
        service_path="/sap/opu/odata/sap/API_PLANNED_ORDERS",
    )


class TestODataV2Connector:
    @respx.mock
    @pytest.mark.asyncio
    async def test_read_with_filter(self, connector):
        """测试 GET 请求 + $filter 构造"""
        respx.get(
            "https://REDACTED-SAP-TENANT.example.com/sap/opu/odata/sap/API_PLANNED_ORDERS/A_PlannedOrder"
            "?$filter=PlannedOrderType eq 'PE'&$top=100&$format=json"
        ).respond(
            json={
                "d": {
                    "results": [
                        {"PlannedOrder": "0010000001", "Material": "FG-001"}
                    ]
                }
            }
        )

        result = await connector.read(
            entity="A_PlannedOrder",
            filter_str="PlannedOrderType eq 'PE'",
            top=100,
        )

        assert len(result["d"]["results"]) == 1
        assert result["d"]["results"][0]["PlannedOrder"] == "0010000001"

    @respx.mock
    @pytest.mark.asyncio
    async def test_authentication_header(self, connector):
        """测试 Basic Auth 头是否正确发送"""
        route = respx.get(
            "https://REDACTED-SAP-TENANT.example.com/sap/opu/odata/sap/API_PLANNED_ORDERS/A_PlannedOrder"
        ).respond(json={"d": {"results": []}})

        await connector.read(entity="A_PlannedOrder")

        request = route.calls[0].request
        assert "Authorization" in request.headers
        assert request.headers["Authorization"].startswith("Basic ")

    @respx.mock
    @pytest.mark.asyncio
    async def test_handle_403_forbidden(self, connector):
        """测试 403 权限不足时的错误处理"""
        respx.get(
            "https://REDACTED-SAP-TENANT.example.com/sap/opu/odata/sap/API_PLANNED_ORDERS/A_PlannedOrder"
        ).respond(status_code=403, json={"error": {"message": {"value": "No authorization"}}})

        with pytest.raises(PermissionError, match="No authorization"):
            await connector.read(entity="A_PlannedOrder")

    @respx.mock
    @pytest.mark.asyncio
    async def test_handle_429_rate_limit(self, connector):
        """测试 429 限流时的重试逻辑"""
        respx.get(
            "https://REDACTED-SAP-TENANT.example.com/sap/opu/odata/sap/API_PLANNED_ORDERS/A_PlannedOrder"
        ).respond(status_code=429, headers={"Retry-After": "5"})

        with pytest.raises(Exception) as exc_info:
            await connector.read(entity="A_PlannedOrder", max_retries=1)
        assert "rate limit" in str(exc_info.value).lower() or "429" in str(exc_info.value)
```

### OData v4 连接器测试（INT-02/04/09）

```python
# backend/tests/integration/test_connector/test_odata_v4_connector.py
# v4 差异：JSON 默认（无 $format）、$count 路径、contains() 替代 substringof()

@respx.mock
@pytest.mark.asyncio
async def test_v4_read_purchase_order(v4_connector):
    respx.get(
        "https://REDACTED-SAP-TENANT.example.com"
        "/sap/opu/odata4/sap/api_purchaseorder_2/srvd_a2x/sap/purchaseorder/0001/"
        "PurchaseOrder?$filter=PurchaseOrderType eq 'NB'&$top=50"
    ).respond(json={"value": [{"PurchaseOrder": "4500000001", "Supplier": "0010000001"}]})

    result = await v4_connector.read(
        entity="PurchaseOrder",
        filter_str="PurchaseOrderType eq 'NB'",
        top=50,
    )
    assert result["value"][0]["PurchaseOrder"] == "4500000001"
```

### 关键测试点

| 测试项 | v2 | v4 |
|--------|----|----|
| URL 构造 | `/sap/opu/odata/sap/{service}/{entity}` | `/sap/opu/odata4/sap/{service}/srvd_a2x/sap/{service_name}/{version}/{entity}` |
| 响应格式 | `{"d": {"results": [...]}}` | `{"value": [...]}` |
| $filter 字符串函数 | `substringof('x', Field)` | `contains(Field, 'x')` |
| 分页 | `__next` URL | `@odata.nextLink` |
| $format | 需要 `$format=json` | 默认 JSON，不需要 |
| 计数 | `$inlinecount=allpages` | `/$count` 后缀 |

---

## L3 — 集成测试（真实租户，只读优先）

### 目标

针对真实 SAP S/4HANA Cloud 租户验证 API 可达性、认证、数据结构。

### 前提

- SAP 凭证文件 `Integration/user.txt` 已配置
- 网络可访问 `REDACTED-SAP-TENANT.example.com`
- **使用单独的 pytest marker `@pytest.mark.sap`**，不混入常规 CI

### 测试配置

```python
# backend/tests/integration/conftest.py
import os
import pytest
from app.integration.connector.odata_connector import ODataV2Connector, ODataV4Connector

def load_sap_credentials():
    """从 user.txt 加载凭证"""
    cred_file = os.getenv("SAP_CREDENTIALS_FILE", "Integration/user.txt")
    with open(cred_file) as f:
        lines = f.read().strip().split("\n")
    # 解析格式：host / client / user / password
    return {
        "base_url": f"https://{lines[0]}",
        "client": lines[1],
        "user": lines[2],
        "password": lines[3],
    }


@pytest.fixture(scope="session")
def sap_credentials():
    return load_sap_credentials()


@pytest.fixture(scope="session")
def odata_v2_connector(sap_credentials):
    return ODataV2Connector(
        base_url=sap_credentials["base_url"],
        client=sap_credentials["client"],
        auth=(sap_credentials["user"], sap_credentials["password"]),
        service_path="/sap/opu/odata/sap",
    )


@pytest.fixture(scope="session")
def odata_v4_connector(sap_credentials):
    return ODataV4Connector(
        base_url=sap_credentials["base_url"],
        client=sap_credentials["client"],
        auth=(sap_credentials["user"], sap_credentials["password"]),
        service_path="/sap/opu/odata4/sap",
    )
```

### 只读集成测试（安全，不修改 SAP 数据）

```python
# backend/tests/integration/test_scenarios/test_readonly_scenarios.py
import pytest

pytestmark = pytest.mark.sap  # 标记为 SAP 集成测试


class TestINT01_PlannedOrders:
    """INT-01: 计划订单读取"""

    @pytest.mark.asyncio
    async def test_api_reachable(self, odata_v2_connector):
        """验证 API 端点可达"""
        result = await odata_v2_connector.read(
            service="API_PLANNED_ORDERS",
            entity="A_PlannedOrder",
            top=1,
        )
        assert result is not None
        assert "d" in result

    @pytest.mark.asyncio
    async def test_metadata_accessible(self, odata_v2_connector):
        """验证 $metadata 可访问（服务已激活）"""
        result = await odata_v2_connector.get_metadata("API_PLANNED_ORDERS")
        assert result is not None
        assert "EntitySet" in result or "Schema" in result

    @pytest.mark.asyncio
    async def test_filter_query(self, odata_v2_connector):
        """验证 $filter 查询"""
        result = await odata_v2_connector.read(
            service="API_PLANNED_ORDERS",
            entity="A_PlannedOrder",
            filter_str="PlannedOrderType eq 'PE'",
            top=10,
        )
        assert "d" in result
        # 不断言具体数据量（沙箱可能无数据）


class TestINT02_PurchaseOrder:
    """INT-02: 采购订单读取（v4 API）"""

    @pytest.mark.asyncio
    async def test_v4_api_reachable(self, odata_v4_connector):
        """验证 v4 API 端点可达"""
        result = await odata_v4_connector.read(
            service_path="/sap/opu/odata4/sap/api_purchaseorder_2/srvd_a2x/sap/purchaseorder/0001",
            entity="PurchaseOrder",
            top=1,
        )
        assert result is not None
        assert "value" in result  # v4 格式


class TestINT13_BusinessPartner:
    """INT-13: 业务伙伴读取"""

    @pytest.mark.asyncio
    async def test_read_business_partner(self, odata_v2_connector):
        result = await odata_v2_connector.read(
            service="API_BUSINESS_PARTNER",
            entity="A_BusinessPartner",
            top=1,
        )
        assert "d" in result


class TestINT15_Product:
    """INT-15: 物料主数据读取"""

    @pytest.mark.asyncio
    async def test_read_product(self, odata_v2_connector):
        result = await odata_v2_connector.read(
            service="API_PRODUCT_SRV",
            entity="A_Product",
            top=1,
        )
        assert "d" in result
```

### 写操作集成测试（需谨慎，使用标记隔离）

```python
# backend/tests/integration/test_scenarios/test_write_scenarios.py
import pytest

pytestmark = [pytest.mark.sap, pytest.mark.sap_write]  # 双标记：仅手动执行


class TestINT03_PurchaseOrderUpdate:
    """INT-03: 采购订单确认更新（v4 PATCH + Supplier Confirmation）"""

    @pytest.mark.asyncio
    async def test_patch_purchase_order(self, odata_v4_connector):
        """测试 PATCH 更新 PO 字段（需已知 PO 号）"""
        po_number = pytest.config.getoption("--sap-po-number")  # 从命令行传入
        if not po_number:
            pytest.skip("未提供 --sap-po-number 参数")

        result = await odata_v4_connector.patch(
            service_path="/sap/opu/odata4/sap/api_purchaseorder_2/srvd_a2x/sap/purchaseorder/0001",
            entity="PurchaseOrder",
            key=f"('{po_number}')",
            data={"PurchaseOrderNote": "EPC Test Update"},
        )
        assert result is not None


class TestINT11_SupplierInvoiceCreate:
    """INT-11: 供应商发票创建"""

    @pytest.mark.asyncio
    async def test_create_supplier_invoice(self, odata_v2_connector):
        """测试创建供应商发票（需已知 PO 号）"""
        po_number = pytest.config.getoption("--sap-po-number")
        if not po_number:
            pytest.skip("未提供 --sap-po-number 参数")

        payload = {
            "CompanyCode": "1000",
            "DocumentDate": "/Date(1782336000000)/",
            "PostingDate": "/Date(1782336000000)/",
            "InvoicingParty": "0010000001",
            "DocumentCurrency": "CNY",
            "InvoiceGrossAmount": "1.00",
            "SupplierInvoiceItem": [
                {
                    "PurchaseOrder": po_number,
                    "PurchaseOrderItem": "10",
                    "QuantityInPurchaseOrderUnit": "1",
                    "PurchaseOrderQuantityUnit": "EA",
                    "SupplierInvoiceItemAmount": "1.00",
                    "TaxCode": "V1",
                }
            ],
        }

        result = await odata_v2_connector.create(
            service="API_SUPPLIERINVOICE_PROCESS_SRV",
            entity="A_SupplierInvoice",
            data=payload,
        )
        assert result is not None
        assert "SupplierInvoice" in str(result)
```

### 运行方式

```bash
# 运行全部只读集成测试
pytest backend/tests/integration/test_scenarios/test_readonly_scenarios.py -m sap -v

# 运行写操作测试（需手动指定 PO 号）
pytest backend/tests/integration/test_scenarios/test_write_scenarios.py \
  -m sap_write \
  --sap-po-number=4500000001 \
  -v

# 排除 SAP 测试（常规 CI）
pytest -m "not sap and not sap_write"
```

### pytest.ini 配置

```ini
# pytest.ini 追加
[pytest]
markers =
    sap: marks tests as SAP integration tests (deselect with -m "not sap")
    sap_write: marks tests as SAP write tests (deselect with -m "not sap_write")
```

---

## L4 — 端到端测试

### 目标

验证完整链路：平台前端 → 平台后端 → 集成层 → SAP S/4HANA Cloud → 数据回传 → 前端展示。

### 测试场景矩阵

| 场景 | 触发方式 | 验证点 | SAP 数据影响 |
|------|---------|--------|-------------|
| INT-01 计划订单同步 | 定时任务 / 手动触发 | 平台 `planned_order` 表有数据 | 只读 |
| INT-02 采购订单同步 | 定时任务 | 平台 `purchase_order` 表有数据 | 只读 |
| INT-03 PO 确认回传 | 供应商在平台确认 → 回传 SAP | SAP PO 确认选项卡更新 | **写入** |
| INT-07 物料凭证同步 | 定时任务 | 平台 `goods_receipt` 表有数据 | 只读 |
| INT-11 发票校验 | 平台发起 → 调 SAP API | SAP 创建发票凭证 | **写入** |
| INT-13 供应商同步 | 定时任务 | 平台 `supplier` 表有数据 | 只读 |
| INT-15 物料同步 | 定时任务 | 平台 `material` 表有数据 | 只读 |

### E2E 测试脚本示例

```python
# backend/tests/integration/test_e2e/test_sync_flow.py
import pytest
import httpx

pytestmark = pytest.mark.sap

BASE_URL = "http://localhost:8000"


class TestSyncFlow:
    """端到端同步流程测试"""

    @pytest.mark.asyncio
    async def test_manual_sync_planned_orders(self):
        """测试手动触发计划订单同步"""
        async with httpx.AsyncClient() as client:
            # 1. 触发同步
            resp = await client.post(f"{BASE_URL}/api/integration/sync/INT-01")
            assert resp.status_code == 202  # Accepted

            task_id = resp.json()["task_id"]

            # 2. 轮询同步状态
            for _ in range(30):  # 最多等 30 秒
                status_resp = await client.get(f"{BASE_URL}/api/integration/sync/status/{task_id}")
                status = status_resp.json()
                if status["state"] in ("completed", "failed"):
                    break
                import asyncio
                await asyncio.sleep(1)

            # 3. 验证同步成功
            assert status["state"] == "completed"
            assert status["records_synced"] >= 0  # 可能为 0（沙箱无数据）

            # 4. 验证数据已落库
            data_resp = await client.get(f"{BASE_URL}/api/planned-orders?limit=1")
            assert data_resp.status_code == 200

    @pytest.mark.asyncio
    async def test_sync_log_recorded(self):
        """验证同步日志已记录"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{BASE_URL}/api/integration/sync-logs?scenario=INT-01&limit=1")
            assert resp.status_code == 200
            logs = resp.json()
            assert len(logs) > 0
            assert logs[0]["scenario_code"] == "INT-01"
            assert logs[0]["status"] in ("success", "partial", "failed")
```

---

## 快速验证脚本（探针）

在集成层代码尚未实现时，用以下脚本快速验证 SAP 租户连通性：

```python
# Integration/probe_sap.py
"""
SAP S/4HANA Cloud API 连通性快速验证脚本
用法: python Integration/probe_sap.py
"""
import httpx
import sys
import os
import json
from datetime import datetime


def load_credentials():
    cred_file = os.getenv("SAP_CREDENTIALS_FILE", "Integration/user.txt")
    with open(cred_file) as f:
        lines = f.read().strip().split("\n")
    return {
        "base_url": f"https://{lines[0]}",
        "client": lines[1],
        "user": lines[2],
        "password": lines[3],
    }


# 需要探测的端点清单
ENDPOINTS = [
    # --- OData v2 (只读) ---
    {
        "name": "INT-01 计划订单",
        "url": "/sap/opu/odata/sap/API_PLANNED_ORDERS/A_PlannedOrder?$top=1",
        "method": "GET",
        "expected": 200,
    },
    {
        "name": "INT-05 采购计划协议",
        "url": "/sap/opu/odata/sap/API_PURCHASING_SCHEDULE_AGREEMENT_SRV/A_SchedgAgrmtHeader?$top=1",
        "method": "GET",
        "expected": 200,
    },
    {
        "name": "INT-07 物料凭证",
        "url": "/sap/opu/odata/sap/API_MATERIAL_DOCUMENT_SRV/A_MaterialDocumentHeader?$top=1",
        "method": "GET",
        "expected": 200,
    },
    {
        "name": "INT-08 检验批",
        "url": "/sap/opu/odata/sap/API_INSPECTIONLOT_SRV/A_InspectionLot?$top=1",
        "method": "GET",
        "expected": 200,
    },
    {
        "name": "INT-13 业务伙伴",
        "url": "/sap/opu/odata/sap/API_BUSINESS_PARTNER/A_BusinessPartner?$top=1",
        "method": "GET",
        "expected": 200,
    },
    {
        "name": "INT-15 物料主数据",
        "url": "/sap/opu/odata/sap/API_PRODUCT_SRV/A_Product?$top=1",
        "method": "GET",
        "expected": 200,
    },
    # --- OData v4 (只读) ---
    {
        "name": "INT-02 采购订单 (v4)",
        "url": "/sap/opu/odata4/sap/api_purchaseorder_2/srvd_a2x/sap/purchaseorder/0001/PurchaseOrder?$top=1",
        "method": "GET",
        "expected": 200,
    },
    # --- OData v2 (写操作) ---
    {
        "name": "INT-11 供应商发票元数据",
        "url": "/sap/opu/odata/sap/API_SUPPLIERINVOICE_PROCESS_SRV/$metadata",
        "method": "GET",
        "expected": 200,
    },
]


def probe():
    creds = load_credentials()
    base = creds["base_url"]
    auth = (creds["user"], creds["password"])
    headers = {
        "sap-client": creds["client"],
        "Accept": "application/json",
    }

    results = []
    for ep in ENDPOINTS:
        url = base + ep["url"]
        try:
            with httpx.Client(verify=False, timeout=30) as client:
                resp = client.request(ep["method"], url, auth=auth, headers=headers)

            status = "✅" if resp.status_code == ep["expected"] else "❌"
            results.append({
                "name": ep["name"],
                "status_code": resp.status_code,
                "expected": ep["expected"],
                "result": status,
                "url": ep["url"],
            })
            print(f"  {status} {ep['name']}: {resp.status_code} (expected {ep['expected']})")
        except Exception as e:
            results.append({
                "name": ep["name"],
                "status_code": "ERROR",
                "expected": ep["expected"],
                "result": "❌",
                "error": str(e),
            })
            print(f"  ❌ {ep['name']}: ERROR - {e}")

    # 保存结果
    output_file = f"Integration/probe-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存到: {output_file}")

    # 汇总
    ok = sum(1 for r in results if r["result"] == "✅")
    fail = sum(1 for r in results if r["result"] == "❌")
    print(f"\n汇总: {ok} OK / {fail} FAIL / {len(results)} TOTAL")


if __name__ == "__main__":
    print(f"SAP S/4HANA Cloud API 连通性验证 — {datetime.now()}\n")
    probe()
```

### 运行探针

```bash
cd D:/AI/采购协同
python Integration/probe_sap.py
```

---

## 测试执行策略

### 开发阶段（当前）

```
┌─────────────────────────────────────────────────┐
│ 1. 运行探针脚本，确认租户连通性                      │
│    python Integration/probe_sap.py               │
├─────────────────────────────────────────────────┤
│ 2. 开发 Adapter，同时编写 L1 单元测试               │
│    pytest backend/tests/integration/test_adapters│
├─────────────────────────────────────────────────┤
│ 3. 开发 Connector，同时编写 L2 契约测试             │
│    pytest backend/tests/integration/test_connector│
├─────────────────────────────────────────────────┤
│ 4. 针对真实租户运行 L3 只读测试                     │
│    pytest -m sap -v                              │
└─────────────────────────────────────────────────┘
```

### CI/CD 策略

| 流水线阶段 | 执行测试 | SAP 依赖 |
|-----------|---------|---------|
| PR 构建 | L1 单元测试 + L2 契约测试 | ❌ 无（Mock） |
| 合并到 main | L1 + L2 + L3 只读 | ✅ 需 VPN/网络可达 |
| 发布前 | L1 + L2 + L3 + L4 E2E | ✅ 需完整环境 |
| 写操作测试 | **仅手动触发** | ✅ 需真实 PO 号 |

### GitHub Actions 配置示例

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  unit-and-contract:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r backend/requirements.txt -r requirements-dev.txt
      - run: pytest -m "not sap and not sap_write" -v

  sap-integration:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'  # 仅 main 分支
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r backend/requirements.txt -r requirements-dev.txt
      - run: pytest -m "sap and not sap_write" -v
        env:
          SAP_CREDENTIALS_FILE: Integration/user.txt
```

---

## 前置检查清单

在开始集成测试前，确认以下事项：

### SAP 侧

- [ ] 通信场景已激活：`SAP_COM_0053`（PO）、`SAP_COM_0057`（发票）、`SAP_COM_0008`（BP）、`SAP_COM_0009`（物料）、`SAP_COM_0108`（物料凭证）
- [ ] 通信用户 `REDACTED_SAP_COMM_USER` 已分配到上述通信场景
- [ ] 通信用户权限包含对应 OData 服务的读权限（写操作需额外授权）
- [ ] OAuth 2.0 客户端已配置（如从 Basic Auth 迁移到 OAuth）

### 平台侧

- [ ] `backend/app/integration/` 模块已创建
- [ ] `backend/app/config.py` 已添加 SAP 配置项
- [ ] `Integration/user.txt` 凭证文件已放置（已 gitignore）
- [ ] `pytest.ini` 已添加 `sap` / `sap_write` marker
- [ ] `requirements-dev.txt` 已添加 `respx`（HTTP mock 库）

### 网络侧

- [ ] 开发环境可访问 `REDACTED-SAP-TENANT.example.com:443`
- [ ] 防火墙/代理不拦截 SAP API 端点
- [ ] SSL 证书验证可通过（或开发环境临时 `verify=False`）

---

## 变更记录

| 日期 | 版本 | 变更内容 | 变更人 |
|------|------|---------|--------|
| 2026-07-06 | V1.0 | 初稿创建，包含 4 层测试策略、探针脚本、CI/CD 配置 | Agent |
