from typing import Protocol

from sentinel.models.reputation import FingerprintRecord, ReputationSignal


class _Cache(Protocol):
    async def get(self, fingerprint: str) -> FingerprintRecord | None: ...
    async def set(self, record: FingerprintRecord, ttl: int = 3600) -> None: ...


class _Store(Protocol):
    async def get(self, fingerprint: str) -> FingerprintRecord | None: ...
    async def upsert(self, record: FingerprintRecord) -> FingerprintRecord: ...


class _Ledger(Protocol):
    async def get(self, fingerprint: str) -> FingerprintRecord | None: ...
    async def enqueue(self, signal: ReputationSignal) -> None: ...


class ReputationRepository:
    """Coordinates hot / warm / cold layers behind a single interface."""

    def __init__(self, cache: _Cache, store: _Store, ledger: _Ledger) -> None:
        self._cache = cache
        self._store = store
        self._ledger = ledger

    async def get(self, fingerprint: str) -> FingerprintRecord | None:
        if record := await self._cache.get(fingerprint):
            return record
        if record := await self._store.get(fingerprint):
            await self._cache.set(record)
            return record
        if record := await self._ledger.get(fingerprint):
            await self._cache.set(record)
            return record
        return None

    async def write_signal(self, signal: ReputationSignal) -> FingerprintRecord:
        merged = await self._store.upsert(
            FingerprintRecord(
                fingerprint=signal.fingerprint,
                score=signal.score,
                operator_id=signal.operator_id,
            )
        )
        await self._cache.set(merged)
        await self._ledger.enqueue(signal)
        return merged
