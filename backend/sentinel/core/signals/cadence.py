import time
from collections import defaultdict, deque
from dataclasses import dataclass, field

from sentinel.core.signals.base import BaseSignal, SignalContext
from sentinel.models.evaluation import EvaluationRequest, SignalResult

WINDOW_SECONDS = 10.0
BURST_THRESHOLD = 15  # requests within window → suspicious


@dataclass
class CadenceCounters:
    """In-memory sliding window of request timestamps per fingerprint."""
    windows: dict[str, deque[float]] = field(
        default_factory=lambda: defaultdict(deque)
    )

    async def record(self, fingerprint: str, ts: float) -> int:
        w = self.windows[fingerprint]
        cutoff = ts - WINDOW_SECONDS
        while w and w[0] < cutoff:
            w.popleft()
        w.append(ts)
        return len(w)


class CadenceSignal(BaseSignal):
    name = "burst_pattern"
    weight = 1.2

    async def evaluate(
        self, req: EvaluationRequest, ctx: SignalContext
    ) -> SignalResult:
        count = await ctx.counters.record(ctx.fingerprint, time.time())
        value = min(1.0, count / BURST_THRESHOLD)
        return SignalResult(
            name=self.name,
            value=value,
            weight=self.weight,
            meta={"window_count": count},
        )
