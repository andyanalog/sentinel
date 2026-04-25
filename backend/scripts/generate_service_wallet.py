"""One-shot: generate the Sentinel service wallet (testnet only).

Creates a fresh EOA, saves the private key to `backend/.secrets/sentinel_service_key.json`
(git-ignored), and prints the address + faucet instructions.

Run once. Fund the printed address at https://faucet.circle.com (Arc Testnet),
then paste the address back so we can write it into `backend/.env` as
`SENTINEL_WALLET_PRIVATE_KEY` for runtime and `DEPLOYER_PRIVATE_KEY` for
the ape deploy script.
"""
from __future__ import annotations

import json
from pathlib import Path

from eth_account import Account

SECRETS = Path(__file__).resolve().parent.parent / ".secrets"
OUT = SECRETS / "sentinel_service_key.json"


def main() -> None:
    SECRETS.mkdir(exist_ok=True)
    if OUT.exists():
        data = json.loads(OUT.read_text())
        print(f"Existing key at {OUT}")
        print(f"Address: {data['address']}")
        return

    acct = Account.create()
    OUT.write_text(json.dumps({"address": acct.address, "private_key": acct.key.hex()}, indent=2))
    OUT.chmod(0o600)

    print("Sentinel service wallet generated.")
    print(f"  Address: {acct.address}")
    print(f"  Key file: {OUT}")
    print()
    print("Next:")
    print("  1. Go to https://faucet.circle.com")
    print("  2. Select 'Arc Testnet'")
    print(f"  3. Paste address: {acct.address}")
    print("  4. Send USDC (used as gas on Arc).")


if __name__ == "__main__":
    main()
