# 待探测端点清单（真实联调前补充验证）

> 以下端点未在 33 端点实测范围内，但 URS 需要它们。真实联调前需用 `probe-sap-connectivity.js` 或手动 curl 补充探测。
> 探测脚本：`D:\AI\ES-MCP-Server\scripts\probe-sap-connectivity.js`

## OData 入站（4 个未探测）

| 场景 | 服务名 | 探测 URL | 通信场景 | 预期 |
|------|--------|---------|---------|------|
| INT-01 采购预测 | `API_PLANNED_ORDERS` | `https://REDACTED-SAP-TENANT.example.com/sap/opu/odata/sap/API_PLANNED_ORDERS/A_PlannedOrder?$top=1&$format=json&sap-client=100` | — | OK 或 403 |
| INT-05 要货计划 | `API_PURCHASING_SCHEDULE_AGREEMENT_SRV` | `https://REDACTED-SAP-TENANT.example.com/sap/opu/odata/sap/API_PURCHASING_SCHEDULE_AGREEMENT_SRV/A_SchedgAgrmt?$top=1&$format=json&sap-client=100` | SAP_COM_0103 | OK 或 403 |
| INT-08 质检结果 | `API_INSPECTIONLOT_SRV` | `https://REDACTED-SAP-TENANT.example.com/sap/opu/odata/sap/API_INSPECTIONLOT_SRV/A_InspectionLot?$top=1&$format=json&sap-client=100` | — | OK 或 403 |
| INT-12 付款状态 | `API_JOURNALENTRY_SRV` | `https://REDACTED-SAP-TENANT.example.com/sap/opu/odata/sap/API_JOURNALENTRY_SRV/A_JournalEntry?$top=1&$format=json&sap-client=100` | — | OK 或 403 |

## RFC/BAPI 出站（2 个，需 SAP Basis 配合）

| 场景 | 函数模块 | 验证方式 | 所需权限 |
|------|---------|---------|---------|
| INT-03 订单确认 | `BAPI_PO_CHANGE` | 通过 SE37 测试或 RFC 客户端调用 | `S_RFC` 权限对象，活动 `16` |
| INT-11 发票校验 | `BAPI_INCOMINGINVOICE_CREATE` | 通过 SE37 测试或 RFC 客户端调用 | `S_RFC` 权限对象，活动 `16` |

## 探测方法

### 方法 1：curl 手动探测

```powershell
# 读取凭证
$user = (Get-Content user.txt | Select-String "Communication User: (\w+)" ).Matches.Groups[1].Value
$pass = Read-Host "请输入 $user 的密码" -AsSecureString
$cred = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("${user}:$($pass)"))

# 探测 INT-01
curl.exe -s -o NUL -w "%{http_code}" `
  -H "Authorization: Basic $cred" `
  -H "Accept: application/json" `
  "https://REDACTED-SAP-TENANT.example.com/sap/opu/odata/sap/API_PLANNED_ORDERS/A_PlannedOrder?`$top=1&`$format=json&sap-client=100"
```

### 方法 2：扩展 probe-sap-connectivity.js

在 `D:\AI\ES-MCP-Server\scripts\probe-sap-connectivity.js` 的端点数组中追加上述 4 个 URL，重跑探测。

### 方法 3：SAP GUI SE37（RFC）

1. 登录 SAP GUI（client 100，用户 REDACTED_SAP_COMM_USER）
2. 事务码 SE37
3. 输入函数模块名（如 `BAPI_PO_CHANGE`）
4. 测试执行，确认无权限错误

## 结果处理

探测完成后，更新本文件和 `README.md` 第 4.3 节的实测状态列。