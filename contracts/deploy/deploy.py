"""Deploy ReputationLedger + OperatorPool to Arc testnet.

Usage:
    ape run contracts/deploy/deploy.py --network arc:testnet

Reads the following env vars:
    SENTINEL_WRITER_ADDRESS   EOA that will call write_batch
    USDC_ADDRESS              USDC token on Arc
    SENTINEL_SERVICE_ADDRESS  EOA that will call pool.debit
"""
import os

from ape import accounts, project


def main():
    deployer = accounts.load("deployer")

    writer = os.environ["SENTINEL_WRITER_ADDRESS"]
    usdc = os.environ["USDC_ADDRESS"]
    sentinel = os.environ["SENTINEL_SERVICE_ADDRESS"]

    ledger = deployer.deploy(project.ReputationLedger, writer)
    pool = deployer.deploy(project.OperatorPool, usdc, sentinel)

    print("ReputationLedger deployed at:", ledger.address)
    print("OperatorPool deployed at:    ", pool.address)
    print()
    print("Add to your .env:")
    print(f"  REPUTATION_LEDGER_ADDRESS={ledger.address}")
    print(f"  OPERATOR_POOL_ADDRESS={pool.address}")
