# 待探测端点清单（真实联调前补充验证）

> 以下端点未在 33 端点实测范围内，或读权限已验证但写权限未验证。真实联调前需补充探测。
> 探测脚本：`D:\AI\ES-MCP-Server\scripts\probe-sap-connectivity.js`
> **部署模型：SAP S/4HANA Public Cloud（公有云），不适用 RFC/BAPI，出站写操作用 OData。**

## OData 入站读取（4 个未探测）

| 场景 | 服务名 | 探测 URL | 通信场景 | 预期 |
|------|--------|---------|---------|------|
| INT-01 采购预测 | `API_PLANNED_ORDERS` | `https://REDACTED-SAP-TENANT.example.com/sap/opu/odata/sap/API_PLANNED_ORDERS/A_PlannedOrder?$top=1&$format=json&sap-client=100` | — | OK 或 403 |
| INT-05 要货计划 | `API_PURCHASING_SCHEDULE_AGREEMENT_SRV` | `https://REDACTED-SAP-TENANT.example.com/sap/opu/odata/sap/API_PURCHASING_SCHEDULE_AGREEMENT_SRV/A_SchedgAgrmt?$top=1&$format=json&sap-client=100` | SAP_COM_0103 | OK 或 403 |
| INT-08 质检结果 | `API_INSPECTIONLOT_SRV` | `https://REDACTED-SAP-TENANT.example.com/sap/opu/odata/sap/API_INSPECTIONLOT_SRV/A_InspectionLot?$top=1&$format=json&sap-client=100` | — | OK 或 403 |
| INT-12 付款状态 | `API_JOURNALENTRY_SRV` | `https://REDACTED-SAP-TENANT.example.com/sap/opu/odata/sap/API_JOURNALENTRY_SRV/A_JournalEntry?$top=1&$format=json&sap-client=100` | — | OK 或 403 |

## OData 出站写权限（3 个，读已 OK 但写未验证）

> ⚠️ 公有云下**读权限 ≠ 写权限**。当前 24 个 OK 端点仅验证了 READ（GET），写操作（PATCH/POST）需 Communication Arrangement 单独开通 CREATE/UPDATE 权限。

| 场景 | 操作 | URL | 通信场景 | 当前读权限 | 写权限 |
|------|------|-----|---------|-----------|--------|
| INT-03 订单确认回传 | V4 **PATCH** | `.../api_purchaseorder_2/srvd_a2x/sap/purchaseorder/0001/PurchaseOrder('{PO}')` | SAP_COM_0053 | ✅ OK | ⚠️ 待验证 UPDATE |
| INT-11 发票校验回传 | V2 **POST** | `.../API_SUPPLIERINVOICE_PROCESS_SRV/A_SupplierInvoice` | legacy V2 | ✅ OK | ⚠️ 待验证 CREATE |
| INT-06 要货确认回传 | V2 **UPDATE** | `.../API_PURCHASING_SCHEDULE_AGREEMENT_SRV/A_SchedgAgrmt` | SAP_COM_0103 | ⚠️ 未探测 | ⚠️ 未探测 |

## ~~RFC/BAPI 出站~~（已废弃，公有云不适用）

> ❌ 以下为 URS 原稿的本地部署方案，本项目为 **S/4HANA Public Cloud**，RFC/BAPI 不可直接调用，已废弃：
> - ~~`BAPI_PO_CHANGE`（ME22N）~~ → 改用 OData V4 PATCH（见上表 INT-03）
> - ~~`BAPI_INCOMINGINVOICE_CREATE`（MIRO）~~ → 改用 OData V2 POST（见上表 INT-11）

## 探测方法

### 方法 1：curl 手动探测（读取）

```powershell
# 读取凭证
$user = (Get-Content user.txt | Select-String "Communication User: (\w+)").Matches.Groups[1].Value
$pass = Read-Host "请输入 $user 的密码" -AsSecureString
$cred = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("${user}:$($pass)"))

# 探测 INT-01（读取）
curl.exe -s -o NUL -w "%{http_code}" `
  -H "Authorization: Basic $cred" `
  -H "Accept: application/json" `
  "https://REDACTED-SAP-TENANT.example.com/sap/opu/odata/sap/API_PLANNED_ORDERS/A_PlannedOrder?`$top=1&`$format=json&sap-client=100"
```

### 方法 2：验证 OData 写权限

写权限无法用 GET 探测，需通过以下方式之一：
1. **SAP Fiori**：检查 Communication Arrangement `SAP_COM_0053` / `SAP_COM_0103` 是否勾选了对应服务的 CREATE/UPDATE 权限
2. **发送测试写请求**：用 curl 发送一个最小 PATCH/POST 请求，观察返回（403=未授权，400=已授权但数据有问题，201/204=成功）
3. **联系 SAP Basis 团队**：确认 `REDACTED_SAP_COMM_USER` 在对应 Arrangement 中的写授权范围

### 方法 3：扩展 probe-sap-connectivity.js

在 `D:\AI\ES-MCP-Server\scripts\probe-sap-connectivity.js` 的端点数组中追加 4 个读取 URL，重跑探测。

## 结果处理

探测完成后，更新本文件、`README.md` 第 0.4 节与第 4.3 节的实测状态列。