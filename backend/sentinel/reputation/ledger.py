"""ArcLedger — cold-layer adapter for the ReputationLedger contract.

Reads (`get`) call `get_record(fingerprint)` directly. Writes (`enqueue` +
`flush`) batch `ReputationSignal`s into a single `write_batch(records[])`
transaction so gas stays bounded per eval.

The adapter is dual-mode:
  - Production: pass an `rpc_url` and the constructor builds its own Web3.
  - Tests: inject a pre-built `Web3` (e.g. one backed by EthereumTesterProvider).

A kill-switch config flag at the container level swaps in DummyLedger if the
RPC is unreachable, so a chain outage never takes the evaluation path down.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import structlog

from sentinel.models.reputation import FingerprintRecord, ReputationSignal

logger = structlog.get_logger(__name__)

_BUNDLED_ABIS = Path(__file__).resolve().parent / "contract_abis.json"
_ARTIFACT_CANDIDATES = [
    # Dev fallback: full Ape build artifact at the monorepo root.
    Path(__file__).resolve().parents[3] / "contracts" / ".build" / "__local__.json",
]


def load_contract_abi(contract_name: str = "ReputationLedger") -> list[dict[str, Any]]:
    """Return the ABI for `contract_name`. Reads the sanitized bundle that
    ships with the backend package; falls back to the full Ape artifact for
    local dev where `ape compile` has been run."""
    if _BUNDLED_ABIS.exists():
        bundle = json.loads(_BUNDLED_ABIS.read_text())
        if contract_name in bundle:
            return bundle[contract_name]["abi"]
    for path in _ARTIFACT_CANDIDATES:
        if path.exists():
            artifact = json.loads(path.read_text())
            return artifact["contractTypes"][contract_name]["abi"]
    raise FileNotFoundError(
        f"ABI for {contract_name} not found. Expected bundle at {_BUNDLED_ABIS} "
        f"or Ape artifact at {_ARTIFACT_CANDIDATES[0]}."
    )


@dataclass
class _PendingWrite:
    fingerprint: bytes   # 32 bytes
    score: int           # 0-100
    reported_by: str     # 0x address
    timestamp: int       # unix seconds


class ArcLedger:
    """Writes batched reputation records to the on-chain ReputationLedger."""

    def __init__(
        self,
        *,
        w3: Any,
        contract_address: str,
        account: Any,
        chain_id: int,
    ) -> None:
        self._w3 = w3
        self._address = contract_address
        self._account = account        # eth_account.LocalAccount or test account
        self._chain_id = chain_id
        self._contract = w3.eth.contract(
            address=contract_address, abi=load_contract_abi()
        )
        self._pending: list[ReputationSignal] = []

    @classmethod
    def from_rpc(
        cls,
        rpc_url: str,
        contract_address: str,
        private_key: str,
        chain_id: int,
    ) -> "ArcLedger":
        from eth_account import Account  # type: ignore
        from web3 import Web3  # type: ignore

        w3 = Web3(Web3.HTTPProvider(rpc_url))
        account = Account.from_key(private_key)
        return cls(
            w3=w3,
            contract_address=contract_address,
            account=account,
            chain_id=chain_id,
        )

    # --- reads ---

    async def get(self, fingerprint: str) -> FingerprintRecord | None:
        """Read the current on-chain score for a fingerprint. Returns None if
        the slot has never been written (sentinel: timestamp == 0)."""
        fp_bytes = _fp_to_bytes32(fingerprint)
        record = self._contract.functions.get_record(fp_bytes).call()
        # record tuple: (fingerprint, score, reported_by, timestamp)
        _, score, reported_by, timestamp = record
        if timestamp == 0:
            return None
        from datetime import datetime, timezone

        return FingerprintRecord(
            fingerprint=fingerprint,
            score=int(score),
            operator_id=reported_by,  # the reporter; operator mapping is off-chain
            last_seen=datetime.fromtimestamp(int(timestamp), tz=timezone.utc),
            signal_count=1,
        )

    # --- writes ---

    async def enqueue(self, signal: ReputationSignal) -> None:
        self._pending.append(signal)

    async def flush(self, batch_size: int = 100) -> list[ReputationSignal]:
        if not self._pending:
            return []
        batch = self._pending[:batch_size]
        self._pending = self._pending[batch_size:]

        records = [
            (
                _fp_to_bytes32(s.fingerprint),
                min(255, max(0, int(s.score))),
                self._account.address,
                int(s.timestamp.timestamp()),
            )
            for s in batch
        ]

        tx = self._contract.functions.write_batch(records).build_transaction(
            {
                "from": self._account.address,
                "nonce": self._w3.eth.get_transaction_count(self._account.address),
                "chainId": self._chain_id,
                "gas": 2_000_000,
                "gasPrice": self._w3.eth.gas_price,
            }
        )
        signed = self._account.sign_transaction(tx)
        # web3 v7 uses raw_transaction; v6 used rawTransaction.
        raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction
        tx_hash = self._w3.eth.send_raw_transaction(raw)
        self._w3.eth.wait_for_transaction_receipt(tx_hash)
        logger.info(
            "arc_ledger.flush",
            count=len(batch),
            contract=self._address,
            tx=tx_hash.hex(),
        )
        return batch


def _fp_to_bytes32(fingerprint: str) -> bytes:
    s = fingerprint.removeprefix("0x")
    # Fingerprints are hex keccak hashes — pad/truncate defensively to 32 bytes.
    if len(s) < 64:
        s = s.ljust(64, "0")
    elif len(s) > 64:
        s = s[:64]
    return bytes.fromhex(s)
