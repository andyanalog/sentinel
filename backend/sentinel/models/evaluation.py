from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Action(str, Enum):
    ALLOW = "ALLOW"
    CHALLENGE = "CHALLENGE"
    BLOCK = "BLOCK"


class EvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    ip: str
    user_agent: str = ""
    path: str = "/"
    method: str = "GET"
    headers: dict[str, str] = Field(default_factory=dict)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    operator_id: str | None = None


class SignalResult(BaseModel):
    name: str
    value: float  # 0.0–1.0, higher = more suspicious
    weight: float = 1.0
    meta: dict[str, float | str | int] = Field(default_factory=dict)


class EvaluationResult(BaseModel):
    action: Action
    score: int  # 0–100
    signals: dict[str, float]
    fingerprint: str
    eval_id: str
