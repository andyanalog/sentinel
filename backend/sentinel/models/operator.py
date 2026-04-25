from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field


class Operator(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    api_key: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class OperatorPool(BaseModel):
    operator_id: str
    balance_usdc: float
    total_evaluations: int = 0
