from dataclasses import dataclass, field

from sentinel.core.signals.cadence import CadenceCounters
from sentinel.core.signals.endpoint import EndpointCounters
from sentinel.core.signals.error_rate import ErrorRateCounters


@dataclass
class Counters:
    """Process-local counters shared by non-repository signals. Survives for
    the lifetime of the FastAPI app, which mirrors a single Redis hot window
    in production."""
    cadence: CadenceCounters = field(default_factory=CadenceCounters)
    endpoints: EndpointCounters = field(default_factory=EndpointCounters)
    errors: ErrorRateCounters = field(default_factory=ErrorRateCounters)

    # CadenceSignal reads via ctx.counters.record — forward to cadence sub-counter
    async def record(self, fingerprint: str, ts: float) -> int:
        return await self.cadence.record(fingerprint, ts)
