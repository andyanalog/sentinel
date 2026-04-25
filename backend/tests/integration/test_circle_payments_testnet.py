"""Phase 4.1 proof of life: credit + debit against the real OperatorPool
deployed on Arc testnet.

Skipped unless `backend/.secrets/testnet_deployment.json` exists and the
service wallet has USDC. Each run uses a unique operator id so repeated
runs don't pile up pool balances.

This test costs a tiny amount of USDC for gas + deposits. Run sparingly.
"""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

import pytest

from sentinel.payments.circle import CirclePayments, _operator_id_to_bytes32

pytestmark = pytest.mark.integration

DEPLOYMENT = (
    Path(__file__).resolve().parents[2] / ".secrets" / "testnet_deployment.json"
)
SERVICE_KEY = (
    Path(__file__).resolve().parents[2] / ".secrets" / "sentinel_service_key.json"
)


@pytest.fixture(scope="module")
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


async def test_operator_id_to_bytes32_is_deterministic():
    a = _operator_id_to_bytes32("op-xyz")
    b = _operator_id_to_bytes32("op-xyz")
    assert a == b and len(a) == 32
    assert _operator_id_to_bytes32("other") != a


async def test_credit_then_debit_roundtrip_onchain(payments: CirclePayments):
    op_id = f"test-{uuid.uuid4()}"
    start = await payments.balance(op_id)
    assert start == 0.0  # fresh operator id

    # 0.01 USDC in, 0.003 USDC out — all well under a cent.
    after_credit = await payments.credit(op_id, 0.01)
    assert pytest.approx(after_credit, abs=1e-6) == 0.01

    after_debit = await payments.debit(op_id, 0.003)
    assert pytest.approx(after_debit, abs=1e-6) == 0.007

    # Confirm a separate balance read sees the same value (no local cache).
    readback = await payments.balance(op_id)
    assert pytest.approx(readback, abs=1e-6) == 0.007
