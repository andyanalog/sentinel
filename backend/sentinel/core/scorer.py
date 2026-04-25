import asyncio
from collections.abc import Sequence

from sentinel.core.signals.base import BaseSignal, SignalContext
from sentinel.models.evaluation import EvaluationRequest, SignalResult


class Scorer:
    """Aggregates signal results into a single 0–100 suspicion score via a
    weighted average. Adding a new signal = append to `signals`. No changes
    here are needed."""

    def __init__(self, signals: Sequence[BaseSignal]) -> None:
        self._signals = list(signals)

    async def score(
        self, req: EvaluationRequest, ctx: SignalContext
    ) -> tuple[int, list[SignalResult]]:
        results = await asyncio.gather(
            *(s.evaluate(req, ctx) for s in self._signals)
        )
        total_weight = sum(r.weight for r in results) or 1.0
        weighted = sum(r.value * r.weight for r in results)
        score = int(round(100 * weighted / total_weight))
        return max(0, min(100, score)), list(results)
