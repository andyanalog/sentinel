"""Phase 4.2: enqueued debits collapse into one on-chain tx per operator
per flush, and the PoolDebitWorker drives the flush on its timer.

Skipped unless `backend/.secrets/testnet_deployment.json` exists.
Costs a small amount of USDC in gas. Uses unique operator ids per run.
"""
from __future__ import annotations

import asyncio
import json
import uuid
from pathlib import Path

import pytest

from sentinel.payments.circle import CirclePayments
from sentinel.workers.pool_debit import PoolDebitWorker

pytestmark = pytest.mark.integration

DEPLOYMENT = (
    Path(__file__).resolve().parents[2] / ".secrets" / "testnet_deployment.json"
)
SERVICE_KEY = (
    Path(__file__).resolve().parents[2] / ".secrets" / "sentinel_service_key.json"
)


@pytest.fixture
def payments() -> CirclePayments:
    if not DEPLOYMENT.exists() or not SERVICE_KEY.exists():
        pytest.skip("testnet deployment artifacts missing; run deploy_testnet.py")
    d = json.loads(DEPLOYMENT.read_text())
    k = json.loads(SERVICE_KEY.read_text())
    return CirclePayments.from_rpc(
        rpc_url=d["rpc_url"],
        pool_address=d["pool"],
        usdc_address=d["usdc"],
        private_key=k["private_key"],
        chain_id=d["chain_id"],
    )


async def test_multiple_debits_collapse_into_single_flush(payments: CirclePayments):
    op_id = f"batch-{uuid.uuid4()}"
    await payments.credit(op_id, 0.01)
    onchain_after_credit = await payments.onchain_balance(op_id)
    assert pytest.approx(onchain_after_credit, abs=1e-6) == 0.01

    # Enqueue 3 debits. None should hit chain yet.
    await payments.debit(op_id, 0.001)
    await payments.debit(op_id, 0.002)
    await payments.debit(op_id, 0.0005)

    # On-chain balance unchanged; projected balance reflects all 3.
    assert pytest.approx(await payments.onchain_balance(op_id), abs=1e-6) == 0.01
    assert pytest.approx(await payments.balance(op_id), abs=1e-6) == 0.0065

    # Flush — expect ONE tx summing to 0.0035 for this operator.
    flushed = await payments.flush_debits()
    assert flushed[op_id] == pytest.approx(0.0035, abs=1e-6)

    # Now on-chain reflects the debit; projected == onchain (no pending).
    assert pytest.approx(await payments.onchain_balance(op_id), abs=1e-6) == 0.0065
    assert pytest.approx(await payments.balance(op_id), abs=1e-6) == 0.0065

    # Flushing an empty queue is a no-op.
    assert await payments.flush_debits() == {}


async def test_debit_worker_drains_on_interval(payments: CirclePayments):
    op_id = f"worker-{uuid.uuid4()}"
    await payments.credit(op_id, 0.005)
    await payments.debit(op_id, 0.001)

    worker = PoolDebitWorker(payments, interval_seconds=1)
    worker.start()
    try:
        # Poll on-chain balance until the worker's first tick lands.
        for _ in range(60):
            if await payments.onchain_balance(op_id) < 0.005:
                break
            await asyncio.sleep(0.1)
    finally:
        await worker.stop()

    assert pytest.approx(await payments.onchain_balance(op_id), abs=1e-6) == 0.004
