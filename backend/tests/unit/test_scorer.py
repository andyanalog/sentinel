import pytest

from sentinel.core.decision import decide
from sentinel.core.scorer import Scorer
from sentinel.core.signals.base import BaseSignal, SignalContext
from sentinel.models.evaluation import Action, EvaluationRequest, SignalResult


class _Fixed(BaseSignal):
    def __init__(self, name: str, value: float, weight: float = 1.0):
        self.name = name
        self._value = value
        self.weight = weight

    async def evaluate(self, req, ctx) -> SignalResult:
        return SignalResult(name=self.name, value=self._value, weight=self.weight)


async def test_weighted_average():
    scorer = Scorer([_Fixed("a", 0.2, 1.0), _Fixed("b", 0.8, 3.0)])
    req = EvaluationRequest(ip="1.2.3.4")
    ctx = SignalContext(fingerprint="0x00")
    score, _ = await scorer.score(req, ctx)
    # (0.2*1 + 0.8*3) / 4 = 0.65 → 65
    assert score == 65


def test_decision_thresholds():
    assert decide(10) == Action.ALLOW
    assert decide(50) == Action.CHALLENGE
    assert decide(90) == Action.BLOCK
