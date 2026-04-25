from sentinel.core.counters import Counters
from sentinel.core.signals.base import SignalContext
from sentinel.core.signals.cadence import CadenceSignal
from sentinel.models.evaluation import EvaluationRequest


async def test_cadence_rises_with_burst():
    signal = CadenceSignal()
    counters = Counters()
    ctx = SignalContext(fingerprint="0xabc", counters=counters)
    req = EvaluationRequest(ip="1.2.3.4")

    first = await signal.evaluate(req, ctx)
    for _ in range(20):
        last = await signal.evaluate(req, ctx)

    assert first.value < last.value
    assert last.value == 1.0
