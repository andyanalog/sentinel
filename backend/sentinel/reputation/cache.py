import json
from typing import Protocol

from sentinel.models.reputation import FingerprintRecord


class CacheBackend(Protocol):
    async def get(self, fingerprint: str) -> FingerprintRecord | None: ...
    async def set(self, record: FingerprintRecord, ttl: int = 3600) -> None: ...


class RedisCache:
    """Hot-layer cache. Lazy-imports redis so dummy mode has zero deps."""

    def __init__(self, url: str) -> None:
        from redis.asyncio import Redis  # type: ignore

        self._redis: "Redis" = Redis.from_url(url, decode_responses=True)

    def _key(self, fp: str) -> str:
        return f"sentinel:fp:{fp}"

    async def get(self, fingerprint: str) -> FingerprintRecord | None:
        raw = await self._redis.get(self._key(fingerprint))
        if not raw:
            return None
        return FingerprintRecord.model_validate_json(raw)

    async def set(self, record: FingerprintRecord, ttl: int = 3600) -> None:
        await self._redis.set(
            self._key(record.fingerprint), record.model_dump_json(), ex=ttl
        )

    async def close(self) -> None:
        await self._redis.aclose()
