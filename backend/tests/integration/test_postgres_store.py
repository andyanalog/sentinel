"""Integration test: PostgresStore against a live Postgres.

Skipped unless SENTINEL_TEST_DATABASE_URL is set. Run with:

    docker compose up -d postgres
    cd backend
    SENTINEL_TEST_DATABASE_URL=postgresql+asyncpg://sentinel:sentinel@localhost:5432/sentinel \\
        venv/bin/pytest tests/integration/test_postgres_store.py -v
"""
import os

import pytest
from sqlalchemy import text

from sentinel.db.session import make_engine, make_session_factory
from sentinel.models.reputation import FingerprintRecord
from sentinel.reputation.store import PostgresStore

pytestmark = pytest.mark.integration

DATABASE_URL = os.getenv("SENTINEL_TEST_DATABASE_URL")


@pytest.fixture
async def session_factory():
    if not DATABASE_URL:
        pytest.skip("SENTINEL_TEST_DATABASE_URL not set")
    engine = make_engine(DATABASE_URL)
    factory = make_session_factory(engine)
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE fingerprints"))
    yield factory
    await engine.dispose()


@pytest.fixture
def store(session_factory):
    return PostgresStore(session_factory)


async def test_upsert_inserts_new_fingerprint(store):
    record = FingerprintRecord(
        fingerprint="fp_test_insert", score=50, operator_id="op_x"
    )
    merged = await store.upsert(record)
    assert merged.score == 50
    assert merged.signal_count == 1  # initial record default
    fetched = await store.get("fp_test_insert")
    assert fetched is not None
    assert fetched.score == 50


async def test_upsert_ema_merges_subsequent_writes(store):
    """Repeated upserts must apply the same 70/30 EMA as the on-chain
    ReputationLedger.write_batch. If these two ever drift we've broken the
    cross-tier invariant."""
    fp = "fp_test_ema"
    await store.upsert(FingerprintRecord(fingerprint=fp, score=90, operator_id="op_x"))
    merged = await store.upsert(
        FingerprintRecord(fingerprint=fp, score=10, operator_id="op_x")
    )
    # 0.7 * 90 + 0.3 * 10 = 66  — matches the Vyper assertion in scripts/local_demo.py.
    assert merged.score == 66
    assert merged.signal_count == 2  # insert(1) + one update(+1)


async def test_upsert_survives_reconnect(store, session_factory):
    """Round-trip through a fresh session proves data is durable, not cached
    in the SQLAlchemy identity map."""
    fp = "fp_test_durable"
    await store.upsert(FingerprintRecord(fingerprint=fp, score=42, operator_id="op_x"))

    fresh_store = PostgresStore(session_factory)
    got = await fresh_store.get(fp)
    assert got is not None
    assert got.score == 42


async def test_get_missing_returns_none(store):
    assert await store.get("fp_does_not_exist") is None
