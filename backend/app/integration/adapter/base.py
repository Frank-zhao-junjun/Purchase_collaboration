"""Base adapter contract for inbound/outbound SAP integrations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseAdapter(ABC):
    """Defines the minimal conversion interface for integration adapters."""

    @abstractmethod
    def sap_to_platform(self, raw_sap_data: dict[str, Any]) -> dict[str, Any]:
        """Convert raw SAP payload to platform payload."""

    @abstractmethod
    def platform_to_sap(self, platform_data: dict[str, Any]) -> dict[str, Any]:
        """Convert platform payload to SAP payload."""

    def build_idempotency_key(
        self,
        scenario_code: str,
        raw_sap_data: dict[str, Any],
        mapped_platform_data: dict[str, Any],
    ) -> str:
        """Default inbound idempotency key: SAP doc + line + last changed timestamp."""
        sap_doc_number = (
            raw_sap_data.get("sap_doc_number")
            or raw_sap_data.get("document_number")
            or raw_sap_data.get("PurchaseOrder")
            or raw_sap_data.get("MaterialDocument")
            or raw_sap_data.get("SupplierInvoice")
            or mapped_platform_data.get("sap_doc_number")
            or mapped_platform_data.get("sap_purchase_order_code")
            or mapped_platform_data.get("sap_material_document_code")
            or mapped_platform_data.get("sap_supplier_invoice_code")
            or "UNKNOWN"
        )
        line_item = (
            raw_sap_data.get("line_item")
            or raw_sap_data.get("PurchaseOrderItem")
            or raw_sap_data.get("MaterialDocumentItem")
            or mapped_platform_data.get("line_item")
            or "0"
        )
        changed_at = (
            raw_sap_data.get("last_changed_at")
            or raw_sap_data.get("LastChangeDateTime")
            or raw_sap_data.get("LastChangeDate")
            or mapped_platform_data.get("last_changed_at")
            or "0"
        )
        return f"{scenario_code}:{sap_doc_number}:{line_item}:{changed_at}"
