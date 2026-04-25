"""Deploy + exercise both contracts on the local Ape test network.

Usage:
    cd contracts
    .venv/bin/ape run deploy/local_demo.py --network ::test

This is the "crypto works on my laptop" milestone for Phase 1.5 — it proves
that the Vyper contracts deploy, accept real transactions, and read/write
the state we expect, end-to-end, without any external node or key.
"""
from ape import accounts, project


def main():
    # Ape's `::test` network pre-funds the first 10 accounts with ETH.
    deployer = accounts.test_accounts[0]
    writer = accounts.test_accounts[1]
    operator = accounts.test_accounts[2]
    sentinel_service = accounts.test_accounts[3]

    print("== Deploying contracts ==")
    usdc = deployer.deploy(project.MockERC20)
    ledger = deployer.deploy(project.ReputationLedger, writer)
    pool = deployer.deploy(project.OperatorPool, usdc.address, sentinel_service)
    print(f"  MockERC20:         {usdc.address}")
    print(f"  ReputationLedger:  {ledger.address}")
    print(f"  OperatorPool:      {pool.address}")

    print("\n== ReputationLedger: write + read ==")
    fp_clean = b"\x01" * 32
    fp_abusive = b"\xff" * 32
    batch = [
        (fp_clean, 10, writer.address, 1_700_000_000),
        (fp_abusive, 90, writer.address, 1_700_000_000),
    ]
    ledger.write_batch(batch, sender=writer)
    print(f"  clean fingerprint score:   {ledger.get_score(fp_clean)}")
    print(f"  abusive fingerprint score: {ledger.get_score(fp_abusive)}")
    assert ledger.get_score(fp_clean) == 10
    assert ledger.get_score(fp_abusive) == 90

    # EMA merge: 90 → (90*7 + 10*3)/10 = 66
    ledger.write_batch(
        [(fp_abusive, 10, writer.address, 1_700_000_100)], sender=writer
    )
    merged = ledger.get_score(fp_abusive)
    print(f"  abusive score after EMA merge (90→10): {merged}  (expect 66)")
    assert merged == 66

    print("\n== OperatorPool: deposit, debit, withdraw ==")
    op_id = b"\xab" * 32
    usdc.mint(operator, 1_000_000, sender=operator)           # 1 USDC (6 decimals)
    usdc.approve(pool.address, 1_000_000, sender=operator)
    pool.deposit(op_id, 500_000, sender=operator)
    print(f"  balance after deposit(500_000): {pool.balance_of(op_id)}")
    assert pool.balance_of(op_id) == 500_000

    pool.debit(op_id, 100, sender=sentinel_service)
    print(f"  balance after debit(100):        {pool.balance_of(op_id)}")
    assert pool.balance_of(op_id) == 499_900

    pool.withdraw(op_id, 50_000, sender=operator)
    print(f"  balance after withdraw(50_000):  {pool.balance_of(op_id)}")
    assert pool.balance_of(op_id) == 449_900

    print("\nAll local-chain interactions succeeded.")
