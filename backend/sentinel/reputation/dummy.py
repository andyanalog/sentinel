import uuid
from datetime import datetime, timezone

import structlog

from sentinel.models.reputation import FingerprintRecord, ReputationSignal

logger = structlog.get_logger(__name__)


class DummyCache:
    def __init__(self) -> None:
        self._store: dict[str, FingerprintRecord] = {}

    async def get(self, fingerprint: str) -> FingerprintRecord | None:
        return self._store.get(fingerprint)

    async def set(self, record: FingerprintRecord, ttl: int = 3600) -> None:
        self._store[record.fingerprint] = record

    async def close(self) -> None:
        self._store.clear()


class DummyStore:
    def __init__(self) -> None:
        self._store: dict[str, FingerprintRecord] = {}

    async def get(self, fingerprint: str) -> FingerprintRecord | None:
        return self._store.get(fingerprint)

    async def upsert(self, record: FingerprintRecord) -> FingerprintRecord:
        existing = self._store.get(record.fingerprint)
        if existing is None:
            merged = record.model_copy(update={"signal_count": 1})
        else:
            merged = existing.model_copy(
                update={
                    "score": int(round(0.7 * existing.score + 0.3 * record.score)),
                    "signal_count": existing.signal_count + 1,
                    "last_seen": datetime.now(timezone.utc),
                }
            )
        self._store[record.fingerprint] = merged
        return merged


class DummyLedger:
    """In-process stand-in for the Arc ReputationLedger contract."""

    def __init__(self) -> None:
        self._store: dict[str, FingerprintRecord] = {}
        self._pending: list[ReputationSignal] = []

    async def get(self, fingerprint: str) -> FingerprintRecord | None:
        return self._store.get(fingerprint)

    async def enqueue(self, signal: ReputationSignal) -> None:
        self._pending.append(signal)

    async def flush(self, batch_size: int = 100) -> list[ReputationSignal]:
        if not self._pending:
            return []
        batch = self._pending[:batch_size]
        self._pending = self._pending[batch_size:]
        tx_hash = f"0xdummy_{uuid.uuid4().hex}"
        for s in batch:
            self._store[s.fingerprint] = FingerprintRecord(
                fingerprint=s.fingerprint,
                score=s.score,
                operator_id=s.operator_id,
                last_seen=s.timestamp,
                signal_count=self._store.get(
                    s.fingerprint,
                    FingerprintRecord(
                        fingerprint=s.fingerprint,
                        score=s.score,
                        operator_id=s.operator_id,
                    ),
                ).signal_count
                + 1,
            )
        logger.info(
            "dummy_ledger.write_batch", count=len(batch), tx=tx_hash
        )
        return batch
