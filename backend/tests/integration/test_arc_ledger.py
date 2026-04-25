"""Integration test: ArcLedger against an in-memory eth-tester node using
the ReputationLedger contract compiled by `ape compile`.

This is Phase 3's proof of life: signals enqueued in Python end up as
on-chain state, readable back through the adapter. No testnet, no RPC
server — the whole node runs in-process via py-evm.

Requires the ape artifact at contracts/.build/__local__.json. If that's
missing, the test instructs how to regenerate it.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from eth_account import Account
from web3 import EthereumTesterProvider, Web3

from sentinel.models.reputation import ReputationSignal
from sentinel.reputation.ledger import ArcLedger, load_contract_abi

pytestmark = pytest.mark.integration

ARTIFACT = (
    Path(__file__).resolve().parents[2].parent
    / "contracts"
    / ".build"
    / "__local__.json"
)


@pytest.fixture(scope="module")
def artifact():
    if not ARTIFACT.exists():
        pytest.skip(
            "contracts/.build/__local__.json missing — run `ape compile` "
            "in contracts/ first"
        )
    return json.loads(ARTIFACT.read_text())


@pytest.fixture
def w3_and_deployment(artifact):
    """Fresh in-process chain + freshly deployed ReputationLedger per test
    so state doesn't leak between cases."""
    provider = EthereumTesterProvider()
    w3 = Web3(provider)

    # Deterministic test key; py-evm tester funds it.
    deployer_pk = provider.ethereum_tester.backend.account_keys[0].to_hex()
    writer_pk = provider.ethereum_tester.backend.account_keys[1].to_hex()
    deployer = Account.from_key(deployer_pk)
    writer = Account.from_key(writer_pk)

    ct = artifact["contractTypes"]["ReputationLedger"]
    abi = ct["abi"]
    bytecode = ct["deploymentBytecode"]["bytecode"]

    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    tx = Contract.constructor(writer.address).build_transaction(
        {
            "from": deployer.address,
            "nonce": w3.eth.get_transaction_count(deployer.address),
            "chainId": w3.eth.chain_id,
            "gas": 2_000_000,
            "gasPrice": w3.eth.gas_price,
        }
    )
    signed = deployer.sign_transaction(tx)
    raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction
    tx_hash = w3.eth.send_raw_transaction(raw)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return w3, receipt.contractAddress, writer


def _make_ledger(w3, address, writer):
    return ArcLedger(
        w3=w3, contract_address=address, account=writer, chain_id=w3.eth.chain_id
    )


async def test_abi_loads_from_ape_artifact():
    abi = load_contract_abi()
    names = {item.get("name") for item in abi if item.get("type") == "function"}
    assert "write_batch" in names
    assert "get_score" in names
    assert "get_record" in names


async def test_enqueue_flush_roundtrip(w3_and_deployment):
    w3, address, writer = w3_and_deployment
    ledger = _make_ledger(w3, address, writer)

    fp = "0x" + "aa" * 32
    await ledger.enqueue(
        ReputationSignal(
            fingerprint=fp,
            score=80,
            operator_id="op_test",
            eval_id="ev_x",
            timestamp=datetime(2026, 4, 19, tzinfo=timezone.utc),
        )
    )
    flushed = await ledger.flush()
    assert len(flushed) == 1

    got = await ledger.get(fp)
    assert got is not None
    assert got.score == 80


async def test_ema_merge_on_chain_matches_python(w3_and_deployment):
    """Two flushes of (90, 10) must collapse to 66 — same EMA the Postgres
    store produces. This is the cross-tier invariant."""
    w3, address, writer = w3_and_deployment
    ledger = _make_ledger(w3, address, writer)

    fp = "0x" + "bb" * 32
    now = datetime(2026, 4, 19, tzinfo=timezone.utc)
    await ledger.enqueue(
        ReputationSignal(
            fingerprint=fp, score=90, operator_id="op", eval_id="ev1", timestamp=now
        )
    )
    await ledger.flush()
    await ledger.enqueue(
        ReputationSignal(
            fingerprint=fp, score=10, operator_id="op", eval_id="ev2", timestamp=now
        )
    )
    await ledger.flush()

    got = await ledger.get(fp)
    assert got is not None
    assert got.score == 66


async def test_get_missing_returns_none(w3_and_deployment):
    w3, address, writer = w3_and_deployment
    ledger = _make_ledger(w3, address, writer)
    assert await ledger.get("0x" + "00" * 32) is None


async def test_batch_size_respected(w3_and_deployment):
    w3, address, writer = w3_and_deployment
    ledger = _make_ledger(w3, address, writer)

    for i in range(5):
        await ledger.enqueue(
            ReputationSignal(
                fingerprint=f"0x{i:064x}",
                score=50,
                operator_id="op",
                eval_id=f"ev{i}",
            )
        )
    # Batch caps at 3 — remaining two stay pending for the next flush.
    first = await ledger.flush(batch_size=3)
    second = await ledger.flush(batch_size=3)
    assert len(first) == 3
    assert len(second) == 2
