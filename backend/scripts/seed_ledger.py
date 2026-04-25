"""Seed ReputationLedger with N batched fingerprint writes so the explorer
shows real activity. Each round = 1 onchain `write_batch` tx with K signals.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sentinel.models.reputation import ReputationSignal
from sentinel.reputation.ledger import ArcLedger

SECRETS = Path(__file__).resolve().parent.parent / ".secrets"
DEPLOYMENT = SECRETS / "testnet_deployment.json"
SERVICE_KEY = SECRETS / "sentinel_service_key.json"

ROUNDS = int(sys.argv[1]) if len(sys.argv) > 1 else 30
SIGNALS_PER_ROUND = int(sys.argv[2]) if len(sys.argv) > 2 else 3


def _fp() -> str:
    return "0x" + hashlib.sha256(uuid.uuid4().bytes).hexdigest()


async def main() -> None:
    d = json.loads(DEPLOYMENT.read_text())
    k = json.loads(SERVICE_KEY.read_text())
    ledger = ArcLedger.from_rpc(
        rpc_url=d["rpc_url"],
        contract_address=d["ledger"],
        private_key=k["private_key"],
        chain_id=d["chain_id"],
    )

    print(f"Seeding {ROUNDS} rounds × {SIGNALS_PER_ROUND} signals = {ROUNDS} write_batch txs")
    print(f"Contract: {d['ledger']}")
    for i in range(ROUNDS):
        for _ in range(SIGNALS_PER_ROUND):
            await ledger.enqueue(
                ReputationSignal(
                    fingerprint=_fp(),
                    score=10 + (i * 3) % 90,
                    operator_id=f"demo-op-{i}",
                    eval_id=f"ev_{uuid.uuid4().hex[:16]}",
                    timestamp=datetime.now(timezone.utc),
                )
            )
        try:
            flushed = await ledger.flush(batch_size=SIGNALS_PER_ROUND)
            print(f"  round {i+1:>2}/{ROUNDS}  flushed {len(flushed)} signals")
        except Exception as e:
            print(f"  round {i+1:>2}/{ROUNDS}  FAILED: {e}")
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
