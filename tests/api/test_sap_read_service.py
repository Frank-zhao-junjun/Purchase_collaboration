from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.integration.read_service import SapReadService


class StubSapClient:
    def __init__(self, payload_by_code):
        self.payload_by_code = payload_by_code

    def get_json(self, endpoint, top=1):
        return self.payload_by_code[endpoint.code]


def test_list_materials_maps_core_fields_from_v2_payload():
    service = SapReadService(
        StubSapClient(
            {
                "INT-15": {
                    "d": {
                        "results": [
                            {
                                "Product": "MAT-001",
                                "ProductType": "FERT",
                                "ProductGroup": "L004",
                                "BaseUnit": "EA",
                            }
                        ]
                    }
                }
            }
        )
    )

    rows = service.list_materials()

    assert rows == [
        {
            "sap_material_code": "MAT-001",
            "name": "MAT-001",
            "product_type": "FERT",
            "category": "L004",
            "base_unit": "EA",
        }
    ]


def test_list_business_partners_maps_core_fields_from_v2_payload():
    service = SapReadService(
        StubSapClient(
            {
                "INT-13": {
                    "d": {
                        "results": [
                            {
                                "BusinessPartner": "BP-1000",
                                "OrganizationBPName1": "贵州茅台供应商",
                                "SearchTerm1": "MTGY",
                                "BusinessPartnerCategory": "2",
                            }
                        ]
                    }
                }
            }
        )
    )

    rows = service.list_business_partners()

    assert rows == [
        {
            "sap_business_partner_code": "BP-1000",
            "name": "贵州茅台供应商",
            "search_term": "MTGY",
            "business_partner_category": "2",
        }
    ]


def test_list_purchase_orders_maps_core_fields_from_v4_payload():
    service = SapReadService(
        StubSapClient(
            {
                "INT-02": {
                    "value": [
                        {
                            "PurchaseOrder": "4500000001",
                            "Supplier": "1000001",
                            "CompanyCode": "1000",
                            "PurchasingOrganization": "P100",
                        }
                    ]
                }
            }
        )
    )

    rows = service.list_purchase_orders()

    assert rows == [
        {
            "sap_purchase_order_code": "4500000001",
            "supplier_code": "1000001",
            "company_code": "1000",
            "purchasing_organization": "P100",
        }
    ]


def test_list_planned_orders_maps_core_fields_from_v2_payload():
    service = SapReadService(
        StubSapClient(
            {
                "INT-01": {
                    "d": {
                        "results": [
                            {
                                "PlannedOrder": "20000001",
                                "Material": "MAT-001",
                                "ProductionPlant": "1000",
                                "PlannedOrderType": "LA",
                            }
                        ]
                    }
                }
            }
        )
    )

    rows = service.list_planned_orders()

    assert rows == [
        {
            "sap_planned_order_code": "20000001",
            "material_code": "MAT-001",
            "plant": "1000",
            "planned_order_type": "LA",
        }
    ]


def test_list_material_documents_maps_core_fields_from_v2_payload():
    service = SapReadService(
        StubSapClient(
            {
                "INT-07": {
                    "d": {
                        "results": [
                            {
                                "MaterialDocument": "490000001",
                                "MaterialDocumentYear": "2026",
                                "PostingDate": "/Date(1783209600000)/",
                                "Supplier": "1000001",
                            }
                        ]
                    }
                }
            }
        )
    )

    rows = service.list_material_documents()

    assert rows == [
        {
            "sap_material_document_code": "490000001",
            "year": "2026",
            "posting_date": "/Date(1783209600000)/",
            "supplier_code": "1000001",
        }
    ]


def test_list_supplier_invoices_maps_core_fields_from_v2_payload():
    service = SapReadService(
        StubSapClient(
            {
                "INT-11": {
                    "d": {
                        "results": [
                            {
                                "SupplierInvoice": "5105600101",
                                "FiscalYear": "2025",
                                "CompanyCode": "1000",
                                "SupplierInvoiceIssuerParty": "1000001",
                                "DocumentDate": "/Date(1735689600000)/",
                            }
                        ]
                    }
                }
            }
        )
    )

    rows = service.list_supplier_invoices()

    assert rows == [
        {
            "sap_supplier_invoice_code": "5105600101",
            "fiscal_year": "2025",
            "company_code": "1000",
            "supplier_code": "1000001",
            "document_date": "/Date(1735689600000)/",
        }
    ]