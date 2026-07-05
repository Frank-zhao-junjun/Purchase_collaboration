"""
US 完整矩阵：每个 US 编号对应一条 assert（可有前置 HTTP 调用以准备数据）。

运行方式（任选其一）：

1) 本地开发（SQLite）
   cd backend && python init_db.py && uvicorn app.main:app --host 127.0.0.1 --port 8000
   cd .. && pip install -r requirements-dev.txt
   pytest tests/api/test_user_stories_smoke.py -v

2) Docker 演示/内网部署（PostgreSQL + Nginx）
   项目根目录: .\\scripts\\run-us-tests.ps1
   或验证经前端反代: .\\scripts\\run-us-tests.ps1 -ThroughNginx
   干净库重跑: .\\scripts\\run-us-tests.ps1 -Fresh
   Linux/macOS: ./scripts/run-us-tests.sh 或 ./scripts/run-us-tests.sh --nginx

环境变量 XIJIU_API_BASE 指定 API 根地址（默认 http://127.0.0.1:8000）。

请勿使用 pytest-xdist 并行；用例依赖文件内顺序与共享状态 ST。
首次部署后建议加 -Fresh/--fresh，避免旧数据导致唯一约束冲突。
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta
from types import SimpleNamespace

import httpx
import pytest

BASE = os.environ.get("XIJIU_API_BASE", "http://127.0.0.1:8000")

# 跨用例共享（同文件内按定义顺序执行）
ST = SimpleNamespace()


@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=BASE, timeout=60.0) as c:
        yield c


def _suffix() -> str:
    return uuid.uuid4().hex[:10]


def test_health(client):
    assert client.get("/health").status_code == 200


# --- Phase 1: 供应商准入 ---


def test_us_101_1(client):
    """供应商注册邀请（采购方发起）"""
    s = _suffix()
    r = client.post(
        "/supplier-portal/invitations",
        json={
            "invited_supplier_name": f"矩阵企业{s}",
            "invited_email": f"inv{s}@us-matrix.test",
            "invited_contact_person": "联系人",
            "expiry_days": 7,
            "notes": "US-101-1",
        },
    )
    assert r.status_code == 200
    body = r.json()
    ST.invitation_code = body["invitation_code"]
    ST.invited_email = f"inv{s}@us-matrix.test"
    assert body["status"] == "pending"
    assert len(body["invitation_code"]) == 8
    assert body["invited_email"] == ST.invited_email
    assert body["invited_supplier_name"] == f"矩阵企业{s}"
    assert body["expiry_date"]
    assert body["notes"] == "US-101-1"


def test_us_101_2(client):
    """查看注册邀请（供应商/列表）"""
    r = client.get(
        "/supplier-portal/invitations",
        params={"email": ST.invited_email},
    )
    assert r.status_code == 200
    rows = r.json()
    assert isinstance(rows, list)
    codes = [i["invitation_code"] for i in rows]
    assert ST.invitation_code in codes
    match = next(i for i in rows if i["invitation_code"] == ST.invitation_code)
    assert match["invited_email"] == ST.invited_email
    assert match["status"] == "pending"


def test_us_102_1(client):
    """供应商自助注册"""
    s = _suffix()
    company_name = f"注册公司{s}"
    ucc = f"91110000{s.upper()}MA001"
    r = client.post(
        "/supplier-portal/register",
        json={
            "invitation_code": ST.invitation_code,
            "company_name": company_name,
            "unified_credit_code": ucc,
            "contact_person": "法人",
            "contact_phone": "13800000000",
            "contact_email": f"reg{s}@us-matrix.test",
            "address": "北京市",
            "main_categories": "粮食",
            "annual_capacity": 100.0,
        },
    )
    assert r.status_code == 200
    body = r.json()
    ST.registration_id = body["id"]
    ST.registration_company_name = company_name
    ST.registration_ucc = ucc
    assert body["status"] == "pending_audit"
    assert body["company_name"] == company_name
    assert body["unified_credit_code"] == ucc
    assert body["contact_person"] == "法人"
    inv_rows = client.get(
        "/supplier-portal/invitations",
        params={"email": ST.invited_email},
    ).json()
    inv = next(i for i in inv_rows if i["invitation_code"] == ST.invitation_code)
    assert inv["status"] == "accepted"


def test_us_102_2(client):
    """采购方查看供应商注册"""
    r = client.get(f"/supplier-portal/registrations/{ST.registration_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["company_name"] == ST.registration_company_name
    assert body["unified_credit_code"] == ST.registration_ucc
    assert body["status"] == "pending_audit"
    assert body["contact_person"] == "法人"
    assert body["main_categories"] == "粮食"
    assert body["annual_capacity"] == 100.0
    assert body["invitation"]["invitation_code"] == ST.invitation_code


def test_us_103_1(client):
    """审批供应商注册（通过）"""
    r = client.post(
        f"/supplier-portal/registrations/{ST.registration_id}/audit",
        json={"action": "approve", "opinion": "US-103-1"},
    )
    assert r.status_code == 200


def test_us_103_2(client):
    """驳回后重新提交（供应商）"""
    s = _suffix()
    inv = client.post(
        "/supplier-portal/invitations",
        json={
            "invited_supplier_name": f"驳回流{s}",
            "invited_email": f"rj{s}@us-matrix.test",
            "expiry_days": 7,
        },
    )
    code = inv.json()["invitation_code"]
    reg = client.post(
        "/supplier-portal/register",
        json={
            "invitation_code": code,
            "company_name": f"驳回公司{s}",
            "unified_credit_code": f"92220000{s.upper()}MA002",
            "contact_person": "张",
            "contact_phone": "13900000000",
        },
    )
    rid = reg.json()["id"]
    client.post(
        f"/supplier-portal/registrations/{rid}/audit",
        json={"action": "reject", "opinion": "请补资料 US-103-2"},
    )
    r2 = client.post(
        f"/supplier-portal/registrations/{rid}/resubmit",
        json={
            "company_name": f"驳回公司{s}（已修订）",
            "unified_credit_code": f"92220000{s.upper()}MA002",
            "contact_person": "张",
            "contact_phone": "13900000001",
        },
    )
    assert r2.status_code == 200


def test_us_104_1(client):
    """资格评审项目创建（采购方）"""
    s = _suffix()
    r = client.post(
        "/qualification/projects",
        json={
            "project_name": f"资格评审{s}",
            "target_categories": "原料",
            "target_supplier_ids": [1],
            "deadline": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "notes": "US-104-1",
        },
    )
    assert r.status_code == 200
    ST.qual_project_id = r.json()["id"]


def test_us_104_2(client):
    """供应商查看资格评审项目"""
    r = client.get("/qualification/projects")
    assert r.status_code == 200


def test_us_105_1(client):
    """供应商填写资格问卷"""
    r = client.post(
        f"/qualification/projects/{ST.qual_project_id}/submission",
        json={
            "supplier_id": 1,
            "answers": {"production": {"production_capacity": 1000, "production_lines": 2}},
        },
    )
    assert r.status_code == 200


def test_us_105_2(client):
    """采购方查看供应商提交"""
    r = client.get(f"/qualification/projects/{ST.qual_project_id}/submissions")
    assert r.status_code == 200


def test_us_106_1(client):
    """采购方评审资格（评分）"""
    r = client.post(
        f"/qualification/projects/{ST.qual_project_id}/submissions/1/review",
        json={
            "reviewer_id": 1,
            "tech_score": 80,
            "quality_score": 85,
            "finance_score": 82,
            "opinions": "US-106-1",
        },
    )
    assert r.status_code == 200


def test_us_106_2(client):
    """供应商查看评审/澄清状态"""
    r = client.get(
        f"/qualification/projects/{ST.qual_project_id}/status",
        params={"supplier_id": 1},
    )
    assert r.status_code == 200


def test_us_107_1(client):
    """采购方最终批准资格"""
    r = client.post(
        f"/qualification/projects/{ST.qual_project_id}/approve",
        params={"supplier_id": 1, "opinion": "US-107-1"},
    )
    assert r.status_code == 200


def test_us_107_2(client):
    """供应商查看最终决定"""
    r = client.get(
        f"/qualification/projects/{ST.qual_project_id}/status",
        params={"supplier_id": 1},
    )
    assert r.status_code == 200


def test_us_108_1(client):
    """采购方资质预警列表"""
    r = client.get("/supplier-portal/supplier-alerts")
    assert r.status_code == 200


def test_us_108_2(client):
    """供应商端资质/预警查看"""
    r = client.get("/supplier-portal/suppliers/1/certifications")
    assert r.status_code == 200


def test_us_109_1(client):
    """供应商提交/更新资质证书"""
    exp = (datetime.utcnow() + timedelta(days=365)).isoformat()
    r = client.post(
        "/supplier-portal/suppliers/1/certifications",
        json={
            "cert_type": "生产许可证",
            "cert_name": "US-109-1 测试证",
            "cert_no": f"CN-US109-{_suffix()}",
            "expiry_date": exp,
        },
    )
    assert r.status_code == 200


def test_us_109_2(client):
    """采购方查看供应商资质"""
    r = client.get("/supplier-portal/suppliers/1/certifications")
    assert r.status_code == 200


# --- Phase 2: 寻源与合同 ---


def test_us_201_1(client):
    """寻源项目发布"""
    s = _suffix()
    r = client.post(
        "/sourcing/projects",
        json={
            "project_name": f"寻源{s}",
            "sourcing_type": "RFQ",
            "materials_summary": "高粱",
            "invited_supplier_ids": [1],
            "evaluation_criteria": {"price": 0.6},
        },
    )
    assert r.status_code == 200
    ST.sourcing_id = r.json()["id"]


def test_us_201_2(client):
    """供应商查看寻源项目"""
    r = client.get(f"/sourcing/projects/{ST.sourcing_id}")
    assert r.status_code == 200


def test_us_202_1(client):
    """供应商接受寻源邀请"""
    r = client.post(
        f"/sourcing/projects/{ST.sourcing_id}/accept",
        params={"supplier_id": 1},
    )
    assert r.status_code == 200


def test_us_202_2(client):
    """采购方查看邀请响应"""
    r = client.get(f"/sourcing/projects/{ST.sourcing_id}")
    assert r.status_code == 200


def test_us_203_1(client):
    """发布中标/授标结果（含投标、开标）"""
    client.post(
        f"/sourcing/projects/{ST.sourcing_id}/bid",
        json={
            "supplier_id": 1,
            "round_number": 1,
            "bid_data": [{"material_name": "高粱", "unit_price": 8000, "quantity": 10, "subtotal": 80000}],
        },
    )
    client.post(f"/sourcing/projects/{ST.sourcing_id}/open-bids")
    r = client.post(
        f"/sourcing/projects/{ST.sourcing_id}/award",
        params={"winner_supplier_id": 1, "awarded_amount": 80000.0},
    )
    assert r.status_code == 200


def test_us_203_2(client):
    """供应商查看授标结果"""
    r = client.get(f"/sourcing/projects/{ST.sourcing_id}")
    assert r.status_code == 200


def test_us_204_1(client):
    """合同草案生成/发布"""
    r = client.post(
        f"/contracts/generate-from-sourcing/{ST.sourcing_id}",
        params={"supplier_id": 1, "contract_name": "US-204-1采购合同"},
    )
    assert r.status_code == 200
    ST.contract_id = r.json()["id"]


def test_us_204_2(client):
    """供应商查看合同草案"""
    r = client.get(f"/contracts/drafts/{ST.contract_id}")
    assert r.status_code == 200


def test_us_205_1(client):
    """供应商合同修改意见"""
    r = client.post(
        f"/contracts/{ST.contract_id}/feedback",
        params={"party": "supplier", "comment": "US-205-1 请调整付款条款"},
    )
    assert r.status_code == 200


def test_us_205_2(client):
    """采购方查看合同修改意见"""
    r = client.get(f"/contracts/{ST.contract_id}/feedback-items")
    assert r.status_code == 200


def test_us_206_1(client):
    """发起在线签署"""
    r = client.post(
        f"/contracts/{ST.contract_id}/sign-initiate",
        params={"sign_sequence": "supplier_first"},
    )
    assert r.status_code == 200


def test_us_206_2(client):
    """供应商在线签署"""
    r = client.post(
        f"/contracts/{ST.contract_id}/sign",
        params={"party": "supplier"},
    )
    assert r.status_code == 200


def test_us_207_1(client):
    """供应商查看签署状态"""
    r = client.get(f"/contracts/{ST.contract_id}/sign-status")
    assert r.status_code == 200


def test_us_207_2(client):
    """采购方查看签署状态"""
    r = client.get(f"/contracts/{ST.contract_id}/sign-status")
    assert r.status_code == 200


def test_us_208_1(client):
    """采购方修改合同（新草稿合同）"""
    s = _suffix()
    gen = client.post(
        f"/contracts/generate-from-sourcing/{ST.sourcing_id}",
        params={"supplier_id": 1, "contract_name": f"US-208-1-{s}"},
    )
    cid = gen.json()["id"]
    r = client.patch(
        f"/contracts/{cid}",
        params={"contract_name": f"已修改-{s}"},
    )
    assert r.status_code == 200


def test_us_208_2(client):
    """供应商查看合同状态"""
    r = client.get(f"/contracts/{ST.contract_id}")
    assert r.status_code == 200


# --- Phase 3: 预测与执行 ---


def test_us_301_1(client):
    """采购预测发布"""
    ps = datetime.utcnow()
    pe = ps + timedelta(days=60)
    cr = client.post(
        "/collaboration/forecasts",
        json={
            "supplier_id": 1,
            "forecast_period": "US-301-1",
            "period_start": ps.isoformat(),
            "period_end": pe.isoformat(),
            "items_data": [{"material_name": "高粱", "material_id": 1, "quantity": 50}],
        },
    )
    fid = cr.json()["id"]
    r = client.post(f"/collaboration/forecasts/{fid}/publish")
    assert r.status_code == 200
    ST.matrix_forecast_id = fid


def test_us_301_2(client):
    """供应商查看采购预测"""
    r = client.get("/collaboration/forecasts", params={"supplier_id": 1})
    assert r.status_code == 200


def test_us_302_1(client):
    """供应商产能响应"""
    r = client.post(
        f"/collaboration/forecasts/{ST.matrix_forecast_id}/responses",
        json={
            "supplier_id": 1,
            "response_data": [{"committed_qty": 40, "delivery_commitment": "10天"}],
            "risk_summary": "US-302-1",
        },
    )
    assert r.status_code == 200


def test_us_302_2(client):
    """采购方查看产能响应"""
    r = client.get(f"/collaboration/forecasts/{ST.matrix_forecast_id}/responses")
    assert r.status_code == 200


def test_us_303_1(client):
    """采购订单发布（创建）"""
    r = client.post(
        "/purchase-orders/",
        json={
            "supplier_id": 1,
            "expected_delivery_date": (datetime.utcnow() + timedelta(days=14)).isoformat(),
            "notes": "US-303-1",
            "items": [
                {"material_id": 1, "quantity": 1.0, "unit_price": 1000.0, "subtotal": 1000.0}
            ],
        },
    )
    assert r.status_code == 201
    ST.matrix_po_id = r.json()["id"]


def test_us_303_2(client):
    """供应商确认订单"""
    r = client.post(f"/purchase-orders/{ST.matrix_po_id}/supplier-confirm")
    assert r.status_code == 200


def test_us_304_1(client):
    """采购订单变更/关闭"""
    r = client.put(
        f"/purchase-orders/{ST.matrix_po_id}",
        json={"status": "cancelled", "notes": "US-304-1 关闭"},
    )
    assert r.status_code == 200


def test_us_304_2(client):
    """供应商查看订单状态"""
    r = client.get(f"/purchase-orders/{ST.matrix_po_id}")
    assert r.status_code == 200


def test_us_305_1(client):
    """发布要货计划（需未取消订单）"""
    po = client.post(
        "/purchase-orders/",
        json={
            "supplier_id": 1,
            "expected_delivery_date": (datetime.utcnow() + timedelta(days=10)).isoformat(),
            "items": [
                {"material_id": 1, "quantity": 2.0, "unit_price": 1000.0, "subtotal": 2000.0}
            ],
        },
    )
    pid = po.json()["id"]
    ST.delivery_po_id = pid
    r = client.post(
        "/collaboration/delivery-schedules",
        json={
            "po_id": pid,
            "supplier_id": 1,
            "required_date": (datetime.utcnow() + timedelta(days=5)).isoformat(),
            "items_data": [{"material_name": "高粱", "quantity": 2}],
        },
    )
    assert r.status_code == 200
    ST.delivery_schedule_id = r.json()["id"]


def test_us_305_2(client):
    """供应商查看要货计划"""
    r = client.get("/collaboration/delivery-schedules", params={"supplier_id": 1})
    assert r.status_code == 200


def test_us_306_1(client):
    """供应商确认要货计划"""
    r = client.post(
        f"/collaboration/delivery-schedules/{ST.delivery_schedule_id}/supplier-confirm",
        json={"supplier_id": 1, "confirmed": True},
    )
    assert r.status_code == 200


def test_us_306_2(client):
    """采购方查看已确认要货计划"""
    r = client.get("/collaboration/delivery-schedules")
    assert r.status_code == 200


def test_us_307_1(client):
    """供应商创建 ASN"""
    r = client.post(
        "/logistics/shipment-notes/",
        json={
            "purchase_order_id": ST.delivery_po_id,
            "supplier_id": 1,
            "total_quantity": 2,
            "items": [
                {
                    "material_id": 1,
                    "material_name": "高粱",
                    "quantity": 2,
                    "unit": "吨",
                    "batch_no": f"B-{_suffix()}",
                }
            ],
        },
    )
    assert r.status_code == 200
    ST.shipment_note_id = r.json()["id"]


def test_us_307_2(client):
    """采购方查看 ASN"""
    r = client.get("/logistics/shipment-notes/")
    assert r.status_code == 200


def test_us_308_1(client):
    """采购方批准送货计划"""
    client.post(f"/logistics/shipment-notes/{ST.shipment_note_id}/submit")
    r = client.post(f"/logistics/shipment-notes/{ST.shipment_note_id}/approve")
    assert r.status_code == 200


def test_us_308_2(client):
    """供应商查看 ASN 状态"""
    r = client.get(f"/logistics/shipment-notes/{ST.shipment_note_id}")
    assert r.status_code == 200


def test_us_309_1(client):
    """提交装箱单与批次"""
    r = client.post(
        f"/logistics/shipment-notes/{ST.shipment_note_id}/packing-lists",
        json={
            "items": [
                {
                    "material_id": 1,
                    "material_name": "高粱",
                    "quantity": 2,
                    "unit": "吨",
                    "batch_no": f"PK-{_suffix()}",
                }
            ]
        },
    )
    assert r.status_code == 200


def test_us_309_2(client):
    """采购方查看/审批装箱批次明细"""
    r = client.get(f"/logistics/shipment-notes/{ST.shipment_note_id}/packing-lists")
    assert r.status_code == 200


def test_us_310_1(client):
    """发布收货与验收结果（创建入库单）"""
    r = client.post(
        "/logistics/receipts/",
        json={
            "warehouse_id": 1,
            "supplier_id": 1,
            "purchase_order_id": ST.delivery_po_id,
            "remarks": "US-310-1",
            "items": [
                {
                    "material_id": 1,
                    "material_name": "高粱",
                    "quantity": 2,
                    "unit": "吨",
                    "batch_no": "RC-MATRIX",
                    "quality_result": "qualified",
                }
            ],
        },
    )
    assert r.status_code == 200


def test_us_310_2(client):
    """供应商查看收货结果"""
    r = client.get("/logistics/receipts/", params={"supplier_id": 1})
    assert r.status_code == 200


# --- Phase 4: 财务 ---


def test_us_401_1(client):
    """供应商创建并提交结算单"""
    ps = datetime(2026, 4, 1)
    pe = datetime(2026, 4, 15)
    r = client.post(
        "/financial/statements/",
        params={"submit": "true"},
        json={
            "supplier_id": 1,
            "settlement_period": "US-401-1",
            "period_start": ps.isoformat(),
            "period_end": pe.isoformat(),
            "total_amount": 2000.0,
            "receipt_ids": [1],
        },
    )
    assert r.status_code == 200
    ST.matrix_statement_id = r.json()["id"]


def test_us_401_2(client):
    """采购方审核结算单"""
    r = client.post(
        f"/financial/statements/{ST.matrix_statement_id}/buyer-audit",
        json={"action": "approve", "auditor": "pytest", "message": "US-401-2"},
    )
    assert r.status_code == 200


def test_us_402_1(client):
    """供应商修订结算单再次提交"""
    st = client.get(f"/financial/statements/{ST.matrix_statement_id}").json()
    r = client.put(
        f"/financial/statements/{ST.matrix_statement_id}",
        params={"submit": "true"},
        json={
            "supplier_id": st["supplier_id"],
            "period_start": st["period_start"],
            "period_end": st["period_end"],
            "total_amount": st["total_amount"],
            "remarks": (st.get("remarks") or "") + " US-402-1",
        },
    )
    assert r.status_code == 200


def test_us_402_2(client):
    """采购方审核修订后的结算单"""
    r = client.post(
        f"/financial/statements/{ST.matrix_statement_id}/buyer-audit",
        json={"action": "approve", "auditor": "pytest", "message": "US-402-2"},
    )
    assert r.status_code == 200


def test_us_403_1(client):
    """供应商创建发票"""
    r = client.post(
        "/financial/invoices/",
        json={
            "statement_id": ST.matrix_statement_id,
            "supplier_id": 1,
            "amount": 1500.0,
            "tax_amount": 195.0,
            "invoice_type": "VAT_SPECIAL",
        },
    )
    assert r.status_code == 200
    ST.matrix_invoice_id = r.json()["id"]


def test_us_403_2(client):
    """三单匹配 + 发票审批"""
    client.get(f"/financial/invoices/{ST.matrix_invoice_id}/three-way-match")
    r = client.post(
        f"/financial/invoices/{ST.matrix_invoice_id}/approve",
        params={"auditor": "财务"},
    )
    assert r.status_code == 200


def test_us_404_1(client):
    """驳回后重提发票"""
    inv_new = client.post(
        "/financial/invoices/",
        json={
            "statement_id": ST.matrix_statement_id,
            "supplier_id": 1,
            "amount": 100.0,
            "tax_amount": 13.0,
        },
    ).json()["id"]
    client.post(
        f"/financial/invoices/{inv_new}/reject",
        params={"reason": "US-404-1"},
    )
    r = client.post(
        f"/financial/invoices/{inv_new}/resubmit",
        json={
            "supplier_id": 1,
            "statement_id": ST.matrix_statement_id,
            "amount": 120.0,
            "tax_amount": 15.6,
        },
    )
    assert r.status_code == 200
    ST.resubmit_invoice_id = inv_new


def test_us_404_2(client):
    """采购方查看重提后的发票"""
    r = client.get(f"/financial/invoices/{ST.resubmit_invoice_id}")
    assert r.status_code == 200


def test_us_405_1(client):
    """付款状态发布"""
    r = client.post(
        "/financial/payments/",
        json={
            "supplier_id": 1,
            "statement_id": ST.matrix_statement_id,
            "invoice_id": ST.matrix_invoice_id,
            "amount": 500.0,
        },
    )
    assert r.status_code == 200
    ST.matrix_payment_id = r.json()["id"]


def test_us_405_2(client):
    """供应商查询付款"""
    r = client.get("/financial/payments/", params={"supplier_id": 1})
    assert r.status_code == 200


# --- US-501 公告 ---


def test_us_501_1(client):
    """公告发布"""
    r = client.post(
        "/announcements/",
        json={
            "title": "US-501-1 公告",
            "content": "矩阵测试",
            "announcement_type": "announcement",
            "published_by": "pytest",
        },
    )
    assert r.status_code == 200
    ST.announcement_id = r.json()["id"]


def test_us_501_2(client):
    """查看公告并记录已读"""
    client.get(f"/announcements/{ST.announcement_id}")
    r = client.post(
        f"/announcements/{ST.announcement_id}/record-read",
        params={"user_id": 1},
    )
    assert r.status_code == 200
