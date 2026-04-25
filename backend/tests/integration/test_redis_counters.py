"""Integration test: RedisCounters — proves cadence/endpoint/error-rate state
is shared across clients, which is the whole reason to put them behind Redis
instead of a per-process dict.

Skipped unless SENTINEL_TEST_REDIS_URL is set.
"""
import asyncio
import os
import time

import pytest
from redis.asyncio import Redis

from sentinel.core.counters_redis import RedisCounters

pytestmark = pytest.mark.integration

REDIS_URL = os.getenv("SENTINEL_TEST_REDIS_URL")


@pytest.fixture
async def counters():
    if not REDIS_URL:
        pytest.skip("SENTINEL_TEST_REDIS_URL not set")
    r = Redis.from_url(REDIS_URL, decode_responses=True)
    await r.flushdb()
    await r.aclose()
    c = RedisCounters.from_url(REDIS_URL)
    yield c


async def test_cadence_counts_across_clients(counters):
    """Two independent RedisCounters instances see the same window — the
    multi-worker invariant that DummyCounters can't guarantee."""
    other = RedisCounters.from_url(REDIS_URL)

    fp = "fp_cad_shared"
    now = time.time()
    for i in range(5):
        await counters.cadence.record(fp, now + i * 0.01)

    count_from_other = await other.cadence.record(fp, now + 0.1)
    # 5 previous + 1 new = 6
    assert count_from_other == 6


async def test_cadence_drops_old_entries(counters):
    fp = "fp_cad_expire"
    old = time.time() - 30  # way older than WINDOW_SECONDS (10)
    await counters.cadence.record(fp, old)
    now = time.time()
    count = await counters.cadence.record(fp, now)
    # Old entry should be evicted, leaving only `now`.
    assert count == 1


async def test_endpoint_diversity_counts_unique(counters):
    fp = "fp_ep"
    assert await counters.endpoints.record(fp, "/a") == 1
    assert await counters.endpoints.record(fp, "/b") == 2
    assert await counters.endpoints.record(fp, "/a") == 2  # dedup


async def test_error_rate_tracks_ratio(counters):
    fp = "fp_err"
    assert await counters.errors.record(fp, None) == 0.0
    assert await counters.errors.record(fp, 200) == 0.0
    ratio = await counters.errors.record(fp, 500)
    assert ratio == pytest.approx(1 / 3, abs=0.01)
