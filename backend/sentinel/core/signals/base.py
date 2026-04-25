from abc import ABC, abstractmethod
from dataclasses import dataclass

from sentinel.models.evaluation import EvaluationRequest, SignalResult


@dataclass
class SignalContext:
    """Per-evaluation context passed to signals. Holds the fingerprint and any
    shared adapters (reputation repo, in-memory counters) that signals need."""
    fingerprint: str
    reputation_repo: object | None = None
    counters: object | None = None


class BaseSignal(ABC):
    name: str = "base"
    weight: float = 1.0

    @abstractmethod
    async def evaluate(
        self, req: EvaluationRequest, ctx: SignalContext
    ) -> SignalResult: ...
