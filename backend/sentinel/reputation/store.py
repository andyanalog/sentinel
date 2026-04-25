from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from sentinel.db.tables import FingerprintRow
from sentinel.models.reputation import FingerprintRecord


class PostgresStore:
    """Warm-layer durable store for fingerprint records."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sf = session_factory

    async def get(self, fingerprint: str) -> FingerprintRecord | None:
        async with self._sf() as session:
            row = await session.get(FingerprintRow, fingerprint)
            if row is None:
                return None
            return FingerprintRecord(
                fingerprint=row.fingerprint,
                score=row.score,
                operator_id=row.operator_id,
                last_seen=row.last_seen,
                signal_count=row.signal_count,
            )

    async def upsert(self, record: FingerprintRecord) -> FingerprintRecord:
        async with self._sf() as session:
            row = await session.get(FingerprintRow, record.fingerprint)
            if row is None:
                row = FingerprintRow(
                    fingerprint=record.fingerprint,
                    score=record.score,
                    operator_id=record.operator_id,
                    signal_count=record.signal_count,
                    last_seen=datetime.now(timezone.utc),
                )
                session.add(row)
            else:
                # Exponential-moving-average on the score so a single noisy
                # signal can't poison the record.
                row.score = int(round(0.7 * row.score + 0.3 * record.score))
                row.signal_count += 1
                row.last_seen = datetime.now(timezone.utc)
            await session.commit()
            return FingerprintRecord(
                fingerprint=row.fingerprint,
                score=row.score,
                operator_id=row.operator_id,
                last_seen=row.last_seen,
                signal_count=row.signal_count,
            )
