"""Deploy ReputationLedger + OperatorPool to Arc testnet using the Sentinel
service wallet.

Reads the compiled artifact from `contracts/.build/__local__.json` (same one
the backend ABI loader uses) and submits two deploy transactions against
https://rpc.testnet.arc.network (chain id 5042002).

Outputs:
  - backend/.secrets/testnet_deployment.json  ({ledger, pool, block, tx_ledger, tx_pool})
  - prints the .env lines to copy into backend/.env.

Prereqs:
  - backend/.secrets/sentinel_service_key.json present (generate_service_wallet.py)
  - that address funded with a few USDC from https://faucet.circle.com
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from eth_account import Account
from web3 import HTTPProvider, Web3

BACKEND = Path(__file__).resolve().parent.parent
SECRETS = BACKEND / ".secrets"
ARTIFACT = BACKEND.parent / "contracts" / ".build" / "__local__.json"
OUT = SECRETS / "testnet_deployment.json"

RPC_URL = os.environ.get("ARC_RPC_URL", "https://rpc.testnet.arc.network")
CHAIN_ID = int(os.environ.get("ARC_CHAIN_ID", "5042002"))
USDC_ADDRESS = os.environ.get(
    "ARC_USDC_ADDRESS", "0x3600000000000000000000000000000000000000"
)


def _load_account() -> Account:
    key_file = SECRETS / "sentinel_service_key.json"
    if not key_file.exists():
        raise SystemExit(f"missing {key_file} — run generate_service_wallet.py first")
    data = json.loads(key_file.read_text())
    return Account.from_key(data["private_key"])


def _deploy(w3: Web3, account, abi, bytecode, args) -> tuple[str, str]:
    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    tx = Contract.constructor(*args).build_transaction(
        {
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "chainId": CHAIN_ID,
            "gas": 3_000_000,
            "gasPrice": w3.eth.gas_price,
        }
    )
    signed = account.sign_transaction(tx)
    raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction
    tx_hash = w3.eth.send_raw_transaction(raw)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if receipt.status != 1:
        raise SystemExit(f"deploy reverted: {tx_hash.hex()}")
    return receipt.contractAddress, tx_hash.hex()


def main() -> None:
    if not ARTIFACT.exists():
        raise SystemExit(
            f"missing {ARTIFACT} — run `ape compile` in contracts/ first"
        )
    artifact = json.loads(ARTIFACT.read_text())
    types = artifact["contractTypes"]

    account = _load_account()
    w3 = Web3(HTTPProvider(RPC_URL))
    if not w3.is_connected():
        raise SystemExit(f"cannot reach {RPC_URL}")

    balance = w3.eth.get_balance(account.address)
    print(f"Deployer:  {account.address}")
    print(f"Balance:   {balance} wei ({balance / 1e18:.6f} USDC on Arc)")
    if balance == 0:
        raise SystemExit(
            "deployer has no USDC on Arc testnet — fund via "
            "https://faucet.circle.com (Arc Testnet)"
        )

    print("\nDeploying ReputationLedger(writer=deployer)...")
    ledger_addr, ledger_tx = _deploy(
        w3,
        account,
        types["ReputationLedger"]["abi"],
        types["ReputationLedger"]["deploymentBytecode"]["bytecode"],
        [account.address],
    )
    print(f"  address: {ledger_addr}")
    print(f"  tx:      {ledger_tx}")

    print("\nDeploying OperatorPool(usdc, sentinel_service=deployer)...")
    pool_addr, pool_tx = _deploy(
        w3,
        account,
        types["OperatorPool"]["abi"],
        types["OperatorPool"]["deploymentBytecode"]["bytecode"],
        [Web3.to_checksum_address(USDC_ADDRESS), account.address],
    )
    print(f"  address: {pool_addr}")
    print(f"  tx:      {pool_tx}")

    SECRETS.mkdir(exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "chain_id": CHAIN_ID,
                "rpc_url": RPC_URL,
                "deployer": account.address,
                "usdc": USDC_ADDRESS,
                "ledger": ledger_addr,
                "pool": pool_addr,
                "tx_ledger": ledger_tx,
                "tx_pool": pool_tx,
            },
            indent=2,
        )
    )
    print(f"\nSaved deployment info to {OUT}")
    print("\nAppend these to backend/.env:")
    print(f"  ARC_RPC_URL={RPC_URL}")
    print(f"  ARC_CHAIN_ID={CHAIN_ID}")
    print(f"  REPUTATION_LEDGER_ADDRESS={ledger_addr}")
    print(f"  OPERATOR_POOL_ADDRESS={pool_addr}")
    print(
        "  SENTINEL_WALLET_PRIVATE_KEY="
        + json.loads((SECRETS / 'sentinel_service_key.json').read_text())['private_key']
    )


if __name__ == "__main__":
    main()
