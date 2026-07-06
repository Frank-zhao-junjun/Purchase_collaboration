"""Normalized read-only SAP resource service for validated integration endpoints."""

from __future__ import annotations

from typing import Callable

from app.integration.client import SapClient
from app.integration.endpoints import SAP_ENDPOINTS


class SapReadService:
    def __init__(self, client: SapClient):
        self.client = client
        self._resource_loaders: dict[str, Callable[[int], list[dict]]] = {
            "materials": self.list_materials,
            "business-partners": self.list_business_partners,
            "purchase-orders": self.list_purchase_orders,
            "planned-orders": self.list_planned_orders,
            "material-documents": self.list_material_documents,
            "supplier-invoices": self.list_supplier_invoices,
        }

    def list_resource(self, resource_name: str, top: int = 50) -> list[dict]:
        loader = self._resource_loaders.get(resource_name)
        if loader is None:
            raise KeyError(resource_name)
        return loader(top=top)

    def list_materials(self, top: int = 50) -> list[dict]:
        rows = self._extract_rows(self.client.get_json(SAP_ENDPOINTS["INT-15"], top=top))
        return [
            {
                "sap_material_code": row.get("Product"),
                "name": row.get("Product") or row.get("ProductName"),
                "product_type": row.get("ProductType"),
                "category": row.get("ProductGroup"),
                "base_unit": row.get("BaseUnit"),
            }
            for row in rows
        ]

    def list_business_partners(self, top: int = 50) -> list[dict]:
        rows = self._extract_rows(self.client.get_json(SAP_ENDPOINTS["INT-13"], top=top))
        return [
            {
                "sap_business_partner_code": row.get("BusinessPartner"),
                "name": row.get("OrganizationBPName1") or row.get("BusinessPartnerFullName"),
                "search_term": row.get("SearchTerm1"),
                "business_partner_category": row.get("BusinessPartnerCategory"),
            }
            for row in rows
        ]

    def list_purchase_orders(self, top: int = 50) -> list[dict]:
        rows = self._extract_rows(self.client.get_json(SAP_ENDPOINTS["INT-02"], top=top))
        return [
            {
                "sap_purchase_order_code": row.get("PurchaseOrder"),
                "supplier_code": row.get("Supplier"),
                "company_code": row.get("CompanyCode"),
                "purchasing_organization": row.get("PurchasingOrganization"),
            }
            for row in rows
        ]

    def list_planned_orders(self, top: int = 50) -> list[dict]:
        rows = self._extract_rows(self.client.get_json(SAP_ENDPOINTS["INT-01"], top=top))
        return [
            {
                "sap_planned_order_code": row.get("PlannedOrder"),
                "material_code": row.get("Material"),
                "plant": row.get("ProductionPlant"),
                "planned_order_type": row.get("PlannedOrderType"),
            }
            for row in rows
        ]

    def list_material_documents(self, top: int = 50) -> list[dict]:
        rows = self._extract_rows(self.client.get_json(SAP_ENDPOINTS["INT-07"], top=top))
        return [
            {
                "sap_material_document_code": row.get("MaterialDocument"),
                "year": row.get("MaterialDocumentYear"),
                "posting_date": row.get("PostingDate"),
                "supplier_code": row.get("Supplier"),
            }
            for row in rows
        ]

    def list_supplier_invoices(self, top: int = 50) -> list[dict]:
        rows = self._extract_rows(self.client.get_json(SAP_ENDPOINTS["INT-11"], top=top))
        return [
            {
                "sap_supplier_invoice_code": row.get("SupplierInvoice"),
                "fiscal_year": row.get("FiscalYear"),
                "company_code": row.get("CompanyCode"),
                "supplier_code": row.get("SupplierInvoiceIssuerParty"),
                "document_date": row.get("DocumentDate"),
            }
            for row in rows
        ]

    @staticmethod
    def _extract_rows(payload: dict) -> list[dict]:
        if isinstance(payload, dict) and "d" in payload and isinstance(payload["d"], dict):
            results = payload["d"].get("results")
            if isinstance(results, list):
                return results
        if isinstance(payload, dict) and isinstance(payload.get("value"), list):
            return payload["value"]
        return []