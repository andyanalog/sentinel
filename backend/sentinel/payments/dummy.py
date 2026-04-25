from collections import defaultdict

import structlog

logger = structlog.get_logger(__name__)


class DummyPayments:
    """Simulates Circle Nanopayments in-process with a $100 starting balance."""

    def __init__(self, starting_balance: float = 100.0) -> None:
        self._balances: dict[str, float] = defaultdict(lambda: starting_balance)

    async def balance(self, operator_id: str) -> float:
        return self._balances[operator_id]

    async def debit(self, operator_id: str, amount: float) -> float:
        self._balances[operator_id] -= amount
        balance = self._balances[operator_id]
        logger.info(
            "dummy_payments.debit",
            operator=operator_id,
            amount=amount,
            balance=balance,
        )
        return balance

    async def credit(self, operator_id: str, amount: float) -> float:
        self._balances[operator_id] += amount
        return self._balances[operator_id]

    async def flush_debits(self) -> dict[str, float]:
        # Dummy is synchronous — nothing pending to flush.
        return {}

    async def close(self) -> None:
        self._balances.clear()
