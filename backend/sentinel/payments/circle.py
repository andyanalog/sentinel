"""ArcPayments — real on-chain adapter for OperatorPool.

For Phase 4.1 the buyer-side fiat-onramp collapses to the Circle faucet: testnet
USDC appears in the service wallet, we deposit it into OperatorPool on behalf
of an operator. In production the same `credit()` entry point will be called
by the Circle fiat→USDC webhook; the onchain deposit is unchanged.

Phase 4.2 adds **batched debits**: per-eval `debit()` enqueues an intent
locally; `flush_debits()` sums intents per operator and issues one
`OperatorPool.debit` tx per operator per batch. Gas drops from O(N) to
O(distinct-operators) per interval. A background `PoolDebitWorker` drives
the flush cadence.

`balance()` returns `onchain_balance - pending_debits`, so 402 decisions in
the evaluate route see projected balance rather than a stale onchain read —
otherwise a hot operator could run the pool into the red between flushes.

USDC uses 6 decimals on Arc; all public methods accept/return float USDC,
converting internally.
"""
from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any

import structlog
from eth_utils import keccak

from sentinel.reputation.ledger import load_contract_abi

logger = structlog.get_logger(__name__)

USDC_DECIMALS = 6
USDC_ONE = 10**USDC_DECIMALS

_ERC20_ABI = [
    {
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]


def _operator_id_to_bytes32(operator_id: str) -> bytes:
    """Stable mapping from app-level operator_id (string) to the bytes32 key
    the contract indexes on. keccak256 keeps it flat and collision-resistant."""
    return keccak(operator_id.encode("utf-8"))


def _to_micro(amount_usdc: float) -> int:
    return int(round(amount_usdc * USDC_ONE))


def _from_micro(amount_micro: int) -> float:
    return amount_micro / USDC_ONE


class CirclePayments:
    """OperatorPool adapter. Name kept for continuity — Circle USDC still
    flows here, Circle Gateway x402 authorizations plug in at 4.2b."""

    def __init__(
        self,
        *,
        w3: Any,
        pool_address: str,
        usdc_address: str,
        account: Any,
        chain_id: int,
    ) -> None:
        self._w3 = w3
        self._account = account
        self._chain_id = chain_id
        self._pool = w3.eth.contract(
            address=pool_address, abi=load_contract_abi("OperatorPool")
        )
        self._usdc = w3.eth.contract(address=usdc_address, abi=_ERC20_ABI)
        # Micro-USDC pending debit per operator_id, flushed in bulk.
        self._pending_micro: dict[str, int] = defaultdict(int)
        self._lock = asyncio.Lock()

    @classmethod
    def from_rpc(
        cls,
        rpc_url: str,
        pool_address: str,
        usdc_address: str,
        private_key: str,
        chain_id: int,
    ) -> "CirclePayments":
        from eth_account import Account
        from web3 import HTTPProvider, Web3

        w3 = Web3(HTTPProvider(rpc_url))
        return cls(
            w3=w3,
            pool_address=pool_address,
            usdc_address=usdc_address,
            account=Account.from_key(private_key),
            chain_id=chain_id,
        )

    @property
    def pool_address(self) -> str:
        return self._pool.address

    @property
    def usdc_address(self) -> str:
        return self._usdc.address

    # --- reads ---

    async def balance(self, operator_id: str) -> float:
        """Projected balance = on-chain balance minus pending (enqueued but
        not yet settled) debits. Keeps 402 decisions consistent between
        flushes."""
        op_id = _operator_id_to_bytes32(operator_id)
        micro = int(self._pool.functions.balance_of(op_id).call())
        pending = self._pending_micro.get(operator_id, 0)
        return _from_micro(max(0, micro - pending))

    async def onchain_balance(self, operator_id: str) -> float:
        """Raw on-chain balance ignoring local pending debits. Useful for
        settlement verification and dashboards."""
        op_id = _operator_id_to_bytes32(operator_id)
        return _from_micro(int(self._pool.functions.balance_of(op_id).call()))

    # --- writes ---

    async def credit(self, operator_id: str, amount: float) -> float:
        """Deposit `amount` USDC into the pool on behalf of `operator_id`.

        The service wallet is acting as the onramp here (hackathon demo).
        In production this is triggered by the Circle fiat→USDC webhook
        after a card top-up clears.
        """
        micro = _to_micro(amount)
        op_id = _operator_id_to_bytes32(operator_id)

        # Approve pool, then deposit. Two txns; acceptable for a top-up.
        self._send(self._usdc.functions.approve(self._pool.address, micro))
        self._send(self._pool.functions.deposit(op_id, micro))

        new_balance = await self.balance(operator_id)
        logger.info(
            "circle_payments.credit",
            operator=operator_id,
            amount=amount,
            balance=new_balance,
        )
        return new_balance

    async def debit(self, operator_id: str, amount: float) -> float:
        """Enqueue a debit intent. Settlement is deferred to `flush_debits()`
        so the gas cost scales with distinct operators per interval, not
        per evaluation call."""
        async with self._lock:
            self._pending_micro[operator_id] += _to_micro(amount)
        return await self.balance(operator_id)

    async def debit_immediate(self, operator_id: str, amount: float) -> float:
        """Synchronous debit path — one tx per call. Used by admin tooling
        and by tests that assert on-chain state directly without waiting
        for the batch worker."""
        micro = _to_micro(amount)
        op_id = _operator_id_to_bytes32(operator_id)
        self._send(self._pool.functions.debit(op_id, micro))
        return await self.balance(operator_id)

    async def flush_debits(self) -> dict[str, float]:
        """Drain pending debits and submit one `pool.debit` tx per operator.

        Returns `{operator_id: flushed_amount}` on the amounts actually sent
        to chain. On tx failure the operator's pending counter is restored
        so nothing is silently dropped.
        """
        async with self._lock:
            snapshot = dict(self._pending_micro)
            self._pending_micro.clear()

        if not snapshot:
            return {}

        flushed: dict[str, float] = {}
        restore: dict[str, int] = {}
        for operator_id, micro in snapshot.items():
            if micro <= 0:
                continue
            op_id = _operator_id_to_bytes32(operator_id)
            try:
                self._send(self._pool.functions.debit(op_id, micro))
                flushed[operator_id] = _from_micro(micro)
            except Exception as e:  # noqa: BLE001
                logger.error(
                    "circle_payments.flush_debit_failed",
                    operator=operator_id,
                    micro=micro,
                    error=str(e),
                )
                restore[operator_id] = micro

        if restore:
            async with self._lock:
                for op, m in restore.items():
                    self._pending_micro[op] += m

        if flushed:
            logger.info("circle_payments.flush_debits", flushed=flushed)
        return flushed

    async def close(self) -> None:
        return None

    # --- internals ---

    def _send(self, fn_call) -> str:
        tx = fn_call.build_transaction(
            {
                "from": self._account.address,
                "nonce": self._w3.eth.get_transaction_count(self._account.address),
                "chainId": self._chain_id,
                "gas": 500_000,
                "gasPrice": self._w3.eth.gas_price,
            }
        )
        signed = self._account.sign_transaction(tx)
        raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction
        tx_hash = self._w3.eth.send_raw_transaction(raw)
        receipt = self._w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status != 1:
            raise RuntimeError(f"tx reverted: {tx_hash.hex()}")
        return tx_hash.hex()
