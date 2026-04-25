from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from sentinel.db.session import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class OperatorRow(Base):
    __tablename__ = "operators"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    api_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class OperatorPoolRow(Base):
    __tablename__ = "operator_pools"

    operator_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    balance_usdc: Mapped[float] = mapped_column(Float, default=0.0)
    total_evaluations: Mapped[int] = mapped_column(Integer, default=0)


class FingerprintRow(Base):
    __tablename__ = "fingerprints"

    fingerprint: Mapped[str] = mapped_column(String(66), primary_key=True)
    score: Mapped[int] = mapped_column(Integer, default=0)
    operator_id: Mapped[str] = mapped_column(String(64), index=True)
    signal_count: Mapped[int] = mapped_column(Integer, default=0)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
