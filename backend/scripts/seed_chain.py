"""Seed the testnet contracts with N rounds of credit + flush so the
explorer shows real activity for judging. Each round:
  - creates a unique demo operator id
  - deposits CREDIT_AMOUNT USDC (1 onchain tx)
  - simulates EVALS_PER_ROUND debits in-memory
  - flushes them in 1 onchain debit tx
Total onchain txs = 2 * ROUNDS.
"""
from __future__ import annotations

import asyncio
import json
import sys
import uuid
from pathlib import Path

from sentinel.payments.circle import CirclePayments
from sentinel.payments.pool import PoolManager

SECRETS = Path(__file__).resolve().parent.parent / ".secrets"
DEPLOYMENT = SECRETS / "testnet_deployment.json"
SERVICE_KEY = SECRETS / "sentinel_service_key.json"

CREDIT_AMOUNT = 0.001
EVAL_COST = 0.0001
EVALS_PER_ROUND = 5
ROUNDS = int(sys.argv[1]) if len(sys.argv) > 1 else 25


async def main() -> None:
    d = json.loads(DEPLOYMENT.read_text())
    k = json.loads(SERVICE_KEY.read_text())
    payments = CirclePayments.from_rpc(
        rpc_url=d["rpc_url"],
        pool_address=d["pool"],
        usdc_address=d["usdc"],
        private_key=k["private_key"],
        chain_id=d["chain_id"],
    )
    pool = PoolManager(payments, EVAL_COST)

    print(f"Seeding {ROUNDS} rounds = ~{2*ROUNDS} onchain txs to {d['pool']}")
    for i in range(ROUNDS):
        op_id = f"demo-{uuid.uuid4()}"
        try:
            await payments.credit(op_id, CREDIT_AMOUNT)
            for _ in range(EVALS_PER_ROUND):
                await pool.debit_evaluation(op_id)
            flushed = await payments.flush_debits()
            print(f"  round {i+1:>2}/{ROUNDS}  op={op_id[:18]}  credit+flush ok  flushed={flushed}")
        except Exception as e:
            print(f"  round {i+1:>2}/{ROUNDS}  FAILED: {e}")
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
