"""Catalog of SAP S/4HANA integration endpoints validated for this project."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SapEndpoint:
    code: str
    name: str
    path: str
    odata_version: str
    communication_scenario: str | None = None


SAP_ENDPOINTS: dict[str, SapEndpoint] = {
    "INT-01": SapEndpoint(
        code="INT-01",
        name="计划订单",
        path="/sap/opu/odata/sap/API_PLANNED_ORDERS/A_PlannedOrder",
        odata_version="v2",
    ),
    "INT-02": SapEndpoint(
        code="INT-02",
        name="采购订单 V4",
        path="/sap/opu/odata4/sap/api_purchaseorder_2/srvd_a2x/sap/purchaseorder/0001/PurchaseOrder",
        odata_version="v4",
        communication_scenario="SAP_COM_0053",
    ),
    "INT-05": SapEndpoint(
        code="INT-05",
        name="采购计划协议",
        path="/sap/opu/odata/sap/API_PURCHASING_SCHEDULE_AGREEMENT_SRV/A_SchedgAgrmt",
        odata_version="v2",
        communication_scenario="SAP_COM_0103",
    ),
    "INT-07": SapEndpoint(
        code="INT-07",
        name="物料凭证",
        path="/sap/opu/odata/sap/API_MATERIAL_DOCUMENT_SRV/A_MaterialDocumentHeader",
        odata_version="v2",
        communication_scenario="SAP_COM_0108",
    ),
    "INT-08": SapEndpoint(
        code="INT-08",
        name="检验批",
        path="/sap/opu/odata/sap/API_INSPECTIONLOT_SRV/A_InspectionLot",
        odata_version="v2",
    ),
    "INT-11": SapEndpoint(
        code="INT-11",
        name="供应商发票 V2",
        path="/sap/opu/odata/sap/API_SUPPLIERINVOICE_PROCESS_SRV/A_SupplierInvoice",
        odata_version="v2",
    ),
    "INT-13": SapEndpoint(
        code="INT-13",
        name="业务伙伴",
        path="/sap/opu/odata/sap/API_BUSINESS_PARTNER/A_BusinessPartner",
        odata_version="v2",
        communication_scenario="SAP_COM_0008",
    ),
    "INT-15": SapEndpoint(
        code="INT-15",
        name="物料主数据",
        path="/sap/opu/odata/sap/API_PRODUCT_SRV/A_Product",
        odata_version="v2",
        communication_scenario="SAP_COM_0009",
    ),
}