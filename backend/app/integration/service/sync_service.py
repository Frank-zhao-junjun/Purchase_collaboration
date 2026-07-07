"""Inbound sync orchestration service for Phase 0.3."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integration.adapter.base import BaseAdapter
from app.integration.models import IdempotencyRecord, SyncLog, SyncQueue


WriterType = Callable[[str, dict[str, Any], AsyncSession], Awaitable[None]]


class SyncService:
    """Run inbound sync pipeline: pull -> map -> idempotent -> persist -> log."""

    RETRY_INTERVALS_SECONDS = [30, 120, 600, 1800]

    def __init__(
        self,
        connector: Any,
        adapters: dict[str, BaseAdapter],
        writer: WriterType | None = None,
    ):
        self.connector = connector
        self.adapters = adapters
        self.writer = writer or self._noop_writer

    async def run_inbound(self, scenario_code: str, session: AsyncSession) -> dict[str, int]:
        adapter = self.adapters.get(scenario_code)
        if adapter is None:
            raise KeyError(f"Adapter not found for scenario: {scenario_code}")

        processed = 0
        skipped = 0
        queued = 0

        try:
            raw_rows = await self.connector.read(scenario_code, params={})
        except Exception as exc:
            await self._enqueue_retry(
                session=session,
                scenario_code=scenario_code,
                payload={"scenario_code": scenario_code},
                error_message=str(exc),
                retry_count=0,
            )
            await self._write_log(
                session=session,
                scenario_code=scenario_code,
                status="fail",
                error_message=str(exc),
                request_payload={"scenario_code": scenario_code},
                response_payload={},
            )
            await session.commit()
            return {"processed": processed, "skipped": skipped, "queued": queued + 1}

        for raw in raw_rows:
            mapped = adapter.sap_to_platform(raw)
            idempotency_key = adapter.build_idempotency_key(scenario_code, raw, mapped)

            if await self._idempotency_exists(session, idempotency_key):
                skipped += 1
                continue

            try:
                await self.writer(scenario_code, mapped, session)
                session.add(
                    IdempotencyRecord(
                        idempotency_key=idempotency_key,
                        scenario_code=scenario_code,
                    )
                )
                processed += 1
            except Exception as exc:
                await self._enqueue_retry(
                    session=session,
                    scenario_code=scenario_code,
                    payload=mapped,
                    error_message=str(exc),
                    retry_count=0,
                )
                queued += 1

        status = "success" if queued == 0 else "retrying"
        await self._write_log(
            session=session,
            scenario_code=scenario_code,
            status=status,
            error_message="" if queued == 0 else f"{queued} item(s) queued for retry",
            request_payload={"scenario_code": scenario_code, "raw_count": len(raw_rows)},
            response_payload={"processed": processed, "skipped": skipped, "queued": queued},
        )
        await session.commit()
        return {"processed": processed, "skipped": skipped, "queued": queued}

    async def schedule_next_retry(self, queue_item: SyncQueue, session: AsyncSession) -> None:
        """Advance retry schedule using 30s -> 2min -> 10min -> 30min."""
        queue_item.retry_count += 1
        next_retry = self._next_retry_time(queue_item.retry_count)
        queue_item.next_retry_time = next_retry
        queue_item.status = "pending"
        await session.flush()

    async def _enqueue_retry(
        self,
        session: AsyncSession,
        scenario_code: str,
        payload: dict[str, Any],
        error_message: str,
        retry_count: int,
    ) -> None:
        session.add(
            SyncQueue(
                scenario_code=scenario_code,
                payload=json.dumps(payload, ensure_ascii=False),
                status="pending",
                retry_count=retry_count,
                next_retry_time=self._next_retry_time(retry_count),
                last_error=error_message,
            )
        )
        await session.flush()

    async def _idempotency_exists(self, session: AsyncSession, idempotency_key: str) -> bool:
        result = await session.execute(
            select(IdempotencyRecord).where(IdempotencyRecord.idempotency_key == idempotency_key)
        )
        return result.scalar_one_or_none() is not None

    async def _write_log(
        self,
        session: AsyncSession,
        scenario_code: str,
        status: str,
        error_message: str,
        request_payload: dict[str, Any],
        response_payload: dict[str, Any],
    ) -> None:
        session.add(
            SyncLog(
                scenario_code=scenario_code,
                direction="inbound",
                status=status,
                error_message=error_message,
                request_payload=json.dumps(request_payload, ensure_ascii=False),
                response_payload=json.dumps(response_payload, ensure_ascii=False),
            )
        )
        await session.flush()

    @classmethod
    def _next_retry_time(cls, retry_count: int) -> datetime:
        index = retry_count if retry_count < len(cls.RETRY_INTERVALS_SECONDS) else len(cls.RETRY_INTERVALS_SECONDS) - 1
        return datetime.utcnow() + timedelta(seconds=cls.RETRY_INTERVALS_SECONDS[index])

    @staticmethod
    async def _noop_writer(_: str, __: dict[str, Any], ___: AsyncSession) -> None:
        return None
