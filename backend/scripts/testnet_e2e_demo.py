"""Phase 4.3 proof: card → pool credit → simulated evals → balance drop,
all against the real OperatorPool on Arc testnet.

No FastAPI / Postgres / Redis needed — this script wires CirclePayments and
PoolManager directly, then simulates N evaluation debits through the same
pool path the /v1/evaluate route uses.

Usage:
    cd backend
    SSL_CERT_FILE=$(./venv/bin/python -c "import certifi; print(certifi.where())") \\
        ./venv/bin/python scripts/testnet_e2e_demo.py

Output is a step-by-step trace with on-chain balance after each phase. The
final on-chain balance should equal `initial_credit − N × eval_cost`, proving
the full credit → eval → flush → settle loop end-to-end.
"""
from __future__ import annotations

import asyncio
import json
import uuid
from pathlib import Path

from sentinel.payments.circle import CirclePayments
from sentinel.payments.pool import PoolManager

SECRETS = Path(__file__).resolve().parent.parent / ".secrets"
DEPLOYMENT = SECRETS / "testnet_deployment.json"
SERVICE_KEY = SECRETS / "sentinel_service_key.json"

CREDIT_AMOUNT = 0.01           # USDC deposited into the pool upfront
EVAL_COST = 0.0001              # USDC per evaluation (matches EVAL_COST_USDC default)
N_EVALS = 20                    # simulated evaluation calls


async def main() -> None:
    if not DEPLOYMENT.exists() or not SERVICE_KEY.exists():
        raise SystemExit("run deploy_testnet.py first")

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

    op_id = f"demo-{uuid.uuid4()}"
    print(f"Operator: {op_id}")
    print(f"Pool contract: {d['pool']}")
    print(f"Explorer: https://testnet.arcscan.app/address/{d['pool']}")
    print()

    print(f"[1] Credit pool with {CREDIT_AMOUNT} USDC (card → pool onramp)...")
    balance = await payments.credit(op_id, CREDIT_AMOUNT)
    print(f"    projected balance: {balance:.6f} USDC")
    print(f"    on-chain balance:  {await payments.onchain_balance(op_id):.6f} USDC")
    print()

    print(f"[2] Simulate {N_EVALS} evaluations at {EVAL_COST} USDC each "
          "(enqueue-only, zero onchain txns)...")
    for i in range(N_EVALS):
        await pool.debit_evaluation(op_id)
        if (i + 1) % 5 == 0:
            projected = await payments.balance(op_id)
            onchain = await payments.onchain_balance(op_id)
            print(f"    after {i + 1:>2}: projected={projected:.6f}  onchain={onchain:.6f}")
    print()

    print("[3] Flush pending debits to chain (one tx per operator)...")
    flushed = await payments.flush_debits()
    print(f"    flushed: {flushed}")
    print()

    final_projected = await payments.balance(op_id)
    final_onchain = await payments.onchain_balance(op_id)
    print("[4] Final state:")
    print(f"    projected balance: {final_projected:.6f} USDC")
    print(f"    on-chain balance:  {final_onchain:.6f} USDC")

    expected = CREDIT_AMOUNT - N_EVALS * EVAL_COST
    print(f"    expected:          {expected:.6f} USDC")
    assert abs(final_onchain - expected) < 1e-6, "on-chain balance drift"
    print()
    print("End-to-end success: card → pool → evals → settle → balance matches.")


if __name__ == "__main__":
    asyncio.run(main())
