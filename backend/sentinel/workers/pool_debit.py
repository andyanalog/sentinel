"""PoolDebitWorker — periodic flush of CirclePayments pending debits.

Mirror of LedgerBatchWorker but for payments: drains per-operator accrued
debits to one `OperatorPool.debit` tx per operator per interval. Keeps
per-eval gas cost at zero; the only onchain cost is the flush.
"""
from __future__ import annotations

import asyncio
from typing import Protocol

import structlog

logger = structlog.get_logger(__name__)


class _Payments(Protocol):
    async def flush_debits(self) -> dict[str, float]: ...


class PoolDebitWorker:
    def __init__(self, payments: _Payments, interval_seconds: int) -> None:
        self._payments = payments
        self._interval = interval_seconds
        self._task: asyncio.Task[None] | None = None
        self._stop = asyncio.Event()

    async def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                await self._payments.flush_debits()
            except Exception as e:  # noqa: BLE001
                logger.error("pool_debit.flush_failed", error=str(e))
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=self._interval)
            except asyncio.TimeoutError:
                continue

    def start(self) -> None:
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self._stop.set()
        if self._task is not None:
            await self._task
