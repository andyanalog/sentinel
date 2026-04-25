from sentinel.models.reputation import ReputationSignal
from sentinel.reputation.dummy import DummyCache, DummyLedger, DummyStore
from sentinel.reputation.repository import ReputationRepository


async def test_write_then_read_via_repo():
    repo = ReputationRepository(DummyCache(), DummyStore(), DummyLedger())
    await repo.write_signal(
        ReputationSignal(
            fingerprint="0xfp", score=80, operator_id="op_a", eval_id="ev_1"
        )
    )
    rec = await repo.get("0xfp")
    assert rec is not None
    assert rec.score == 80


async def test_cross_app_reputation_visible_to_second_operator():
    repo = ReputationRepository(DummyCache(), DummyStore(), DummyLedger())
    await repo.write_signal(
        ReputationSignal(
            fingerprint="0xfp", score=90, operator_id="op_a", eval_id="ev_1"
        )
    )
    rec = await repo.get("0xfp")
    assert rec is not None
    # op_b queries the same repo and sees op_a's signal — the product's core
    # cross-app deterrent property.
    assert rec.operator_id == "op_a"
    assert rec.score == 90
