from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.integration.adapter.base import BaseAdapter
from app.integration.models import Base, IdempotencyRecord, SyncLog, SyncQueue
from app.integration.service.sync_service import SyncService


class FakeInboundConnector:
    def __init__(self, rows=None, error: Exception | None = None):
        self.rows = rows or []
        self.error = error

    async def read(self, scenario_code, params):
        assert isinstance(params, dict)
        if self.error:
            raise self.error
        return self.rows


class FakeAdapter(BaseAdapter):
    def sap_to_platform(self, raw_sap_data):
        return {
            "sap_doc_number": raw_sap_data["sap_doc_number"],
            "line_item": raw_sap_data.get("line_item", "0"),
            "last_changed_at": raw_sap_data.get("last_changed_at", "0"),
            "value": raw_sap_data.get("value", ""),
        }

    def platform_to_sap(self, platform_data):
        return dict(platform_data)


def _run(coro):
    return asyncio.run(coro)


def _new_session_factory(tmp_path: Path):
    db_path = tmp_path / "sync_service_test.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def init_schema():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    _run(init_schema())
    return engine, session_factory


def test_run_inbound_success_persists_idempotency_and_logs(tmp_path: Path):
    engine, session_factory = _new_session_factory(tmp_path)
    stored_payloads: list[dict] = []

    async def writer(_, payload, __):
        stored_payloads.append(payload)

    service = SyncService(
        connector=FakeInboundConnector(
            rows=[
                {"sap_doc_number": "4500000010", "line_item": "10", "last_changed_at": "2026-07-06T10:00:00Z", "value": "A"},
                {"sap_doc_number": "4500000011", "line_item": "20", "last_changed_at": "2026-07-06T10:00:01Z", "value": "B"},
            ]
        ),
        adapters={"INT-02": FakeAdapter()},
        writer=writer,
    )

    async def run_test():
        async with session_factory() as session:
            result = await service.run_inbound("INT-02", session)
            assert result == {"processed": 2, "skipped": 0, "queued": 0}

            idem_rows = (await session.execute(select(IdempotencyRecord))).scalars().all()
            assert len(idem_rows) == 2

            log_rows = (await session.execute(select(SyncLog))).scalars().all()
            assert len(log_rows) == 1
            assert log_rows[0].status == "success"

    _run(run_test())
    assert len(stored_payloads) == 2
    _run(engine.dispose())


def test_run_inbound_skips_duplicate_rows_by_idempotency(tmp_path: Path):
    engine, session_factory = _new_session_factory(tmp_path)
    stored_payloads: list[dict] = []

    async def writer(_, payload, __):
        stored_payloads.append(payload)

    rows = [{"sap_doc_number": "4500000100", "line_item": "10", "last_changed_at": "2026-07-06T11:00:00Z", "value": "A"}]

    service = SyncService(
        connector=FakeInboundConnector(rows=rows),
        adapters={"INT-02": FakeAdapter()},
        writer=writer,
    )

    async def run_test():
        async with session_factory() as session:
            first = await service.run_inbound("INT-02", session)
            second = await service.run_inbound("INT-02", session)

            assert first == {"processed": 1, "skipped": 0, "queued": 0}
            assert second == {"processed": 0, "skipped": 1, "queued": 0}

            idem_rows = (await session.execute(select(IdempotencyRecord))).scalars().all()
            assert len(idem_rows) == 1

    _run(run_test())
    assert len(stored_payloads) == 1
    _run(engine.dispose())


def test_run_inbound_enqueue_retry_when_pull_fails(tmp_path: Path):
    engine, session_factory = _new_session_factory(tmp_path)

    service = SyncService(
        connector=FakeInboundConnector(error=RuntimeError("SAP timeout")),
        adapters={"INT-07": FakeAdapter()},
    )

    async def run_test():
        async with session_factory() as session:
            before = datetime.utcnow()
            result = await service.run_inbound("INT-07", session)
            after = datetime.utcnow()

            assert result == {"processed": 0, "skipped": 0, "queued": 1}

            queue_rows = (await session.execute(select(SyncQueue))).scalars().all()
            assert len(queue_rows) == 1
            assert queue_rows[0].retry_count == 0
            assert queue_rows[0].status == "pending"
            assert queue_rows[0].last_error == "SAP timeout"
            lower = before.timestamp() + 25
            upper = after.timestamp() + 35
            assert lower <= queue_rows[0].next_retry_time.timestamp() <= upper

            log_rows = (await session.execute(select(SyncLog))).scalars().all()
            assert len(log_rows) == 1
            assert log_rows[0].status == "fail"

    _run(run_test())
    _run(engine.dispose())