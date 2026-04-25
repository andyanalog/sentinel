from collections import defaultdict
from dataclasses import dataclass, field

from sentinel.core.signals.base import BaseSignal, SignalContext
from sentinel.models.evaluation import EvaluationRequest, SignalResult


@dataclass
class EndpointCounters:
    paths: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))

    async def record(self, fingerprint: str, path: str) -> int:
        self.paths[fingerprint].add(path)
        return len(self.paths[fingerprint])


class EndpointDiversitySignal(BaseSignal):
    """Flags low-diversity callers hammering a single endpoint."""
    name = "endpoint_diversity"
    weight = 0.5

    async def evaluate(
        self, req: EvaluationRequest, ctx: SignalContext
    ) -> SignalResult:
        counters = getattr(ctx.counters, "endpoints", None) or _NOOP
        distinct = await counters.record(ctx.fingerprint, req.path)
        value = 1.0 if distinct == 1 else max(0.0, 1.0 - (distinct - 1) / 5)
        return SignalResult(name=self.name, value=value, weight=self.weight)


_NOOP = EndpointCounters()
