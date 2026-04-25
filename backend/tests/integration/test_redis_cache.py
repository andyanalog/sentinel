"""Integration test: RedisCache against a live Redis.

Skipped unless SENTINEL_TEST_REDIS_URL is set. Run with:

    docker compose up -d redis
    cd backend
    SENTINEL_TEST_REDIS_URL=redis://localhost:6379/0 \\
        venv/bin/pytest tests/integration/test_redis_cache.py -v
"""
import asyncio
import os

import pytest

from sentinel.models.reputation import FingerprintRecord
from sentinel.reputation.cache import RedisCache

pytestmark = pytest.mark.integration

REDIS_URL = os.getenv("SENTINEL_TEST_REDIS_URL")


@pytest.fixture
async def cache():
    if not REDIS_URL:
        pytest.skip("SENTINEL_TEST_REDIS_URL not set")
    c = RedisCache(REDIS_URL)
    # Clear namespace so tests are independent of prior runs.
    await c._redis.flushdb()
    yield c
    await c.close()


async def test_roundtrip_set_get(cache):
    rec = FingerprintRecord(fingerprint="fp_rt", score=73, operator_id="op_x")
    await cache.set(rec)
    got = await cache.get("fp_rt")
    assert got is not None
    assert got.fingerprint == "fp_rt"
    assert got.score == 73


async def test_missing_returns_none(cache):
    assert await cache.get("fp_nope") is None


async def test_ttl_expires(cache):
    rec = FingerprintRecord(fingerprint="fp_ttl", score=10, operator_id="op_x")
    await cache.set(rec, ttl=1)
    assert await cache.get("fp_ttl") is not None
    await asyncio.sleep(1.2)
    assert await cache.get("fp_ttl") is None


async def test_two_clients_see_same_key(cache):
    """Proves Redis state is shared across process-like clients — the whole
    point of Redis over the DummyCache.
    """
    rec = FingerprintRecord(fingerprint="fp_shared", score=55, operator_id="op_x")
    await cache.set(rec)

    other = RedisCache(REDIS_URL)
    try:
        got = await other.get("fp_shared")
        assert got is not None
        assert got.score == 55
    finally:
        await other.close()
