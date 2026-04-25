import asyncio
from typing import Protocol

import structlog

logger = structlog.get_logger(__name__)


class _Ledger(Protocol):
    async def flush(self, batch_size: int = 100) -> list: ...


class LedgerBatchWorker:
    """Periodically flushes pending reputation signals to the cold layer."""

    def __init__(
        self, ledger: _Ledger, interval_seconds: int, batch_size: int
    ) -> None:
        self._ledger = ledger
        self._interval = interval_seconds
        self._batch_size = batch_size
        self._task: asyncio.Task[None] | None = None
        self._stop = asyncio.Event()

    async def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                await self._ledger.flush(self._batch_size)
            except Exception as e:  # noqa: BLE001
                logger.error("ledger_batch.flush_failed", error=str(e))
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
