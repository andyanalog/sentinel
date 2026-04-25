import secrets
import uuid
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from sentinel.db.tables import OperatorPoolRow, OperatorRow
from sentinel.models.operator import Operator


class OperatorRegistry(Protocol):
    async def create(self, name: str) -> Operator: ...
    async def get(self, operator_id: str) -> Operator | None: ...
    async def by_api_key(self, api_key: str) -> Operator | None: ...

    @staticmethod
    def in_memory() -> "OperatorRegistry":
        return _InMemoryRegistry()

    @staticmethod
    def postgres(session_factory: async_sessionmaker[AsyncSession]) -> "OperatorRegistry":
        return _PostgresRegistry(session_factory)


class _InMemoryRegistry:
    def __init__(self) -> None:
        self._by_id: dict[str, Operator] = {}
        self._by_key: dict[str, Operator] = {}

    async def create(self, name: str) -> Operator:
        op = Operator(
            id=f"op_{uuid.uuid4().hex[:10]}",
            name=name,
            api_key=f"sk_{secrets.token_urlsafe(24)}",
        )
        self._by_id[op.id] = op
        self._by_key[op.api_key] = op
        return op

    async def get(self, operator_id: str) -> Operator | None:
        return self._by_id.get(operator_id)

    async def by_api_key(self, api_key: str) -> Operator | None:
        return self._by_key.get(api_key)


class _PostgresRegistry:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sf = session_factory

    async def create(self, name: str) -> Operator:
        op = Operator(
            id=f"op_{uuid.uuid4().hex[:10]}",
            name=name,
            api_key=f"sk_{secrets.token_urlsafe(24)}",
        )
        async with self._sf() as session:
            session.add(OperatorRow(id=op.id, name=op.name, api_key=op.api_key))
            session.add(OperatorPoolRow(operator_id=op.id, balance_usdc=0.0))
            await session.commit()
        return op

    async def get(self, operator_id: str) -> Operator | None:
        async with self._sf() as session:
            row = await session.get(OperatorRow, operator_id)
            return Operator.model_validate(row) if row else None

    async def by_api_key(self, api_key: str) -> Operator | None:
        from sqlalchemy import select

        async with self._sf() as session:
            result = await session.execute(
                select(OperatorRow).where(OperatorRow.api_key == api_key)
            )
            row = result.scalar_one_or_none()
            return Operator.model_validate(row) if row else None
