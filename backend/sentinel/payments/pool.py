from typing import Protocol

import structlog

logger = structlog.get_logger(__name__)


class InsufficientFundsError(RuntimeError):
    def __init__(self, operator_id: str, balance: float) -> None:
        super().__init__(f"operator {operator_id} pool empty ({balance} USDC)")
        self.operator_id = operator_id
        self.balance = balance


class _Payments(Protocol):
    async def balance(self, operator_id: str) -> float: ...
    async def debit(self, operator_id: str, amount: float) -> float: ...
    async def credit(self, operator_id: str, amount: float) -> float: ...


class PoolManager:
    """Wraps the payments adapter with the per-evaluation debit policy."""

    def __init__(self, payments: _Payments, eval_cost: float) -> None:
        self._payments = payments
        self._cost = eval_cost

    async def debit_evaluation(self, operator_id: str) -> float:
        balance = await self._payments.balance(operator_id)
        if balance < self._cost:
            raise InsufficientFundsError(operator_id, balance)
        return await self._payments.debit(operator_id, self._cost)

    async def credit(self, operator_id: str, amount: float) -> float:
        return await self._payments.credit(operator_id, amount)

    async def balance(self, operator_id: str) -> float:
        return await self._payments.balance(operator_id)
