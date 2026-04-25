from collections import defaultdict
from dataclasses import dataclass, field

from sentinel.core.signals.base import BaseSignal, SignalContext
from sentinel.models.evaluation import EvaluationRequest, SignalResult


@dataclass
class ErrorRateCounters:
    total: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    errors: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    async def record(self, fingerprint: str, status_hint: int | None) -> float:
        self.total[fingerprint] += 1
        if status_hint is not None and status_hint >= 400:
            self.errors[fingerprint] += 1
        return self.errors[fingerprint] / max(1, self.total[fingerprint])


class ErrorRateSignal(BaseSignal):
    name = "error_rate"
    weight = 0.7

    async def evaluate(
        self, req: EvaluationRequest, ctx: SignalContext
    ) -> SignalResult:
        counters = getattr(ctx.counters, "errors", None) or _NOOP
        hint_raw = req.headers.get("x-prev-status")
        hint = int(hint_raw) if hint_raw and hint_raw.isdigit() else None
        ratio = await counters.record(ctx.fingerprint, hint)
        return SignalResult(name=self.name, value=min(1.0, ratio), weight=self.weight)


_NOOP = ErrorRateCounters()
