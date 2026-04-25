from sentinel.core.signals.base import SignalContext
from sentinel.core.signals.reputation import ReputationSignal
from sentinel.models.evaluation import EvaluationRequest
from sentinel.models.reputation import FingerprintRecord, ReputationSignal as RepSig
from sentinel.reputation.dummy import DummyCache, DummyLedger, DummyStore
from sentinel.reputation.repository import ReputationRepository


async def test_unseen_fingerprint_scores_zero():
    repo = ReputationRepository(DummyCache(), DummyStore(), DummyLedger())
    ctx = SignalContext(fingerprint="0xnew", reputation_repo=repo)
    res = await ReputationSignal().evaluate(EvaluationRequest(ip="1.1.1.1"), ctx)
    assert res.value == 0.0


async def test_prior_bad_score_drives_signal_high():
    repo = ReputationRepository(DummyCache(), DummyStore(), DummyLedger())
    await repo.write_signal(
        RepSig(fingerprint="0xbad", score=90, operator_id="op_a", eval_id="ev1")
    )
    ctx = SignalContext(fingerprint="0xbad", reputation_repo=repo)
    res = await ReputationSignal().evaluate(EvaluationRequest(ip="1.1.1.1"), ctx)
    assert res.value >= 0.8
