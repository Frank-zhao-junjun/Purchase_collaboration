# SAP S/4HANA 集成层 — 权威参考手册

> **单一信息源（Single Source of Truth）**：本文件汇总 SAP 集成层实现所需的全部权威数据。

## 集成架构

本项目与 SAP S/4HANA Cloud 系统通过 OData API 进行集成。

### 部署模型

| 项 | 值 |
|----|-----|
| **产品** | SAP S/4HANA Cloud, Public Edition（公有云版） |
| **集成方式** | OData V2/V4 API（通过通信场景授权） |

### 配置方式

SAP 连接配置通过环境变量设置（见 `backend/app/config.py`）：

| 环境变量 | 说明 |
|---------|------|
| SAP_BASE_URL | SAP API 根地址（通过环境变量设置） |
| SAP_CLIENT | sap-client 查询参数 |
| SAP_COMM_USER | 通信用户 |
| SAP_COMM_PASSWORD | 通信用户密码（通过环境变量设置） |
| SAP_CREDENTIALS_FILE | 凭证文件路径（可选） |

## 已确认的 SAP OData 端点

| 编号 | 名称 | OData 版本 | 通信场景 |
|------|------|-----------|---------|
| INT-01 | 计划订单 | V2 | - |
| INT-02 | 采购订单 | V4 | SAP_COM_0053 |
| INT-05 | 采购计划协议 | V2 | SAP_COM_0103 |
| INT-07 | 物料凭证 | V2 | SAP_COM_0108 |
| INT-08 | 检验批 | V2 | - |
| INT-11 | 供应商发票 | V2 | - |
| INT-13 | 业务伙伴 | V2 | SAP_COM_0008 |
| INT-15 | 物料主数据 | V2 | SAP_COM_0009 |

> **注意**：具体的 SAP 租户 URL、通信用户名和密码属于敏感信息，请通过安全渠道获取并配置到环境变量中。
