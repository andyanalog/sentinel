"""Redis-backed counter implementations.

Matches the async API of CadenceCounters / EndpointCounters / ErrorRateCounters
so signals are oblivious to whether they're talking to an in-memory dict
or a Redis instance shared across uvicorn workers.

Every key carries a TTL so idle fingerprints don't accumulate hot-state
memory indefinitely.
"""
from __future__ import annotations

from dataclasses import dataclass

from redis.asyncio import Redis  # type: ignore

from sentinel.core.signals.cadence import BURST_THRESHOLD, WINDOW_SECONDS  # noqa: F401

_CADENCE_TTL = 120        # seconds; comfortably larger than WINDOW_SECONDS
_ENDPOINT_TTL = 3600
_ERROR_TTL = 3600


def _cadence_key(fp: str) -> str:
    return f"sentinel:cad:{fp}"


def _endpoint_key(fp: str) -> str:
    return f"sentinel:ep:{fp}"


def _total_key(fp: str) -> str:
    return f"sentinel:err:tot:{fp}"


def _err_key(fp: str) -> str:
    return f"sentinel:err:err:{fp}"


class RedisCadenceCounters:
    """Sliding-window burst detector implemented as a sorted set per fingerprint.
    ZADD the timestamp, ZREMRANGEBYSCORE to drop entries older than the window,
    ZCARD to get the current count. All three run in a single pipeline round-trip."""

    def __init__(self, redis: Redis) -> None:
        self._r = redis

    async def record(self, fingerprint: str, ts: float) -> int:
        key = _cadence_key(fingerprint)
        cutoff = ts - WINDOW_SECONDS
        pipe = self._r.pipeline()
        pipe.zremrangebyscore(key, "-inf", cutoff)
        # Score == member so duplicate timestamps (unlikely) collapse cleanly.
        pipe.zadd(key, {str(ts): ts})
        pipe.zcard(key)
        pipe.expire(key, _CADENCE_TTL)
        _, _, count, _ = await pipe.execute()
        return int(count)


class RedisEndpointCounters:
    """Set of paths seen per fingerprint."""

    def __init__(self, redis: Redis) -> None:
        self._r = redis

    async def record(self, fingerprint: str, path: str) -> int:
        key = _endpoint_key(fingerprint)
        pipe = self._r.pipeline()
        pipe.sadd(key, path)
        pipe.scard(key)
        pipe.expire(key, _ENDPOINT_TTL)
        _, distinct, _ = await pipe.execute()
        return int(distinct)


class RedisErrorRateCounters:
    """Running ratio of errors to total requests per fingerprint."""

    def __init__(self, redis: Redis) -> None:
        self._r = redis

    async def record(self, fingerprint: str, status_hint: int | None) -> float:
        pipe = self._r.pipeline()
        pipe.incr(_total_key(fingerprint))
        pipe.expire(_total_key(fingerprint), _ERROR_TTL)
        if status_hint is not None and status_hint >= 400:
            pipe.incr(_err_key(fingerprint))
            pipe.expire(_err_key(fingerprint), _ERROR_TTL)
        results = await pipe.execute()
        total = int(results[0])

        errors_raw = await self._r.get(_err_key(fingerprint))
        errors = int(errors_raw) if errors_raw else 0
        return errors / max(1, total)


@dataclass
class RedisCounters:
    """Drop-in replacement for `Counters` that routes to Redis."""
    cadence: RedisCadenceCounters
    endpoints: RedisEndpointCounters
    errors: RedisErrorRateCounters

    @classmethod
    def from_url(cls, url: str) -> "RedisCounters":
        r = Redis.from_url(url, decode_responses=True)
        return cls(
            cadence=RedisCadenceCounters(r),
            endpoints=RedisEndpointCounters(r),
            errors=RedisErrorRateCounters(r),
        )

    async def record(self, fingerprint: str, ts: float) -> int:
        return await self.cadence.record(fingerprint, ts)
