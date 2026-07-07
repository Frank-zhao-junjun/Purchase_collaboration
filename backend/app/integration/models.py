"""SAP 集成层数据模型

5 张表支撑集成管理需求（INT-M01~M06）：
- sync_logs: 同步日志与审计（INT-M01）
- sync_queue: 重试与补偿队列（INT-M02）
- scenario_configs: 场景开关控制（INT-M05）
- field_mappings: 字段映射配置（INT-M04）
- idempotency_records: 幂等去重（INT-M06）
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, Index

from app.core.database import Base


class SyncLog(Base):
    """同步日志与审计（INT-M01-01/02/04）

    每条同步记录写入日志，含场景编号、方向、SAP/平台单据号、
    同步时间、状态、错误信息、请求/响应报文。
    """
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    scenario_code = Column(String(20), nullable=False, index=True)  # INT-01 ~ INT-15
    direction = Column(String(10), nullable=False)  # inbound / outbound
    sap_doc_number = Column(String(100), index=True)  # SAP 单据号
    platform_doc_number = Column(String(100), index=True)  # 平台单据号
    sync_time = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    status = Column(String(20), nullable=False)  # success / fail / retrying
    error_message = Column(Text, default="")
    request_payload = Column(Text, default="")  # 脱敏后的请求报文
    response_payload = Column(Text, default="")  # 脱敏后的响应报文
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "scenario_code": self.scenario_code,
            "direction": self.direction,
            "sap_doc_number": self.sap_doc_number,
            "platform_doc_number": self.platform_doc_number,
            "sync_time": self.sync_time.isoformat() if self.sync_time else None,
            "status": self.status,
            "error_message": self.error_message,
        }


class SyncQueue(Base):
    """重试与补偿队列（INT-M02-01/02/03/04）

    同步失败时入队，按 30s→2min→10min→30min 重试最多 4 次。
    """
    __tablename__ = "sync_queue"

    id = Column(Integer, primary_key=True, index=True)
    scenario_code = Column(String(20), nullable=False, index=True)
    payload = Column(Text, nullable=False)  # 待同步数据 JSON
    status = Column(String(20), default="pending", nullable=False)  # pending/processing/done/failed
    retry_count = Column(Integer, default=0, nullable=False)
    next_retry_time = Column(DateTime, index=True)  # 下次重试时间
    last_error = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ScenarioConfig(Base):
    """场景开关控制（INT-M05-01/02/03）

    每个集成场景可独立启停，含同步频率与最近同步时间。
    """
    __tablename__ = "scenario_configs"

    id = Column(Integer, primary_key=True, index=True)
    scenario_code = Column(String(20), nullable=False, unique=True, index=True)
    scenario_name = Column(String(100), default="")
    enabled = Column(Boolean, default=True, nullable=False)
    use_mock = Column(Boolean, default=False, nullable=False)  # 403 场景用 Mock
    sync_frequency_seconds = Column(Integer, default=3600)  # 同步频率（秒）
    priority = Column(String(5), default="P1")  # P0/P1
    last_sync_time = Column(DateTime)
    last_sync_status = Column(String(20), default="")  # success/fail
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FieldMapping(Base):
    """字段映射配置（INT-M04-01/02/03）

    定义 SAP 字段 ↔ 平台字段的对应关系，支持简单值转换。
    """
    __tablename__ = "field_mappings"

    id = Column(Integer, primary_key=True, index=True)
    scenario_code = Column(String(20), nullable=False, index=True)
    sap_field = Column(String(100), nullable=False)
    platform_field = Column(String(100), nullable=False)
    transform_rule = Column(Text, default="")  # JSON：值转换/单位转换规则
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class IdempotencyRecord(Base):
    """幂等去重（INT-M06-01/02/03）

    入站：SAP 单据号 + 行项目号 + 最后变更时间戳
    出站：平台单据号 + 操作类型
    重复推送不产生副作用，仅更新最后同步时间。
    """
    __tablename__ = "idempotency_records"

    id = Column(Integer, primary_key=True, index=True)
    idempotency_key = Column(String(255), nullable=False, unique=True, index=True)
    scenario_code = Column(String(20), nullable=False, index=True)
    last_sync_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_idempotency_key_scenario", "idempotency_key", "scenario_code"),
    )