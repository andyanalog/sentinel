from datetime import datetime, timezone

from pydantic import BaseModel, Field


class FingerprintRecord(BaseModel):
    fingerprint: str       # 0x-prefixed keccak hash
    score: int             # 0–100
    operator_id: str
    last_seen: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    signal_count: int = 1


class ReputationSignal(BaseModel):
    fingerprint: str
    score: int
    operator_id: str
    eval_id: str
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
