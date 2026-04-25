from sentinel.core.signals.base import BaseSignal, SignalContext
from sentinel.models.evaluation import EvaluationRequest, SignalResult


class ReputationSignal(BaseSignal):
    """Cross-app reputation lookup via the reputation repository.

    Operates against all three layers (hot → warm → cold) through the same
    repository interface, so it works identically in dummy and production."""
    name = "cross_app_reputation"
    weight = 1.5

    async def evaluate(
        self, req: EvaluationRequest, ctx: SignalContext
    ) -> SignalResult:
        value = 0.0
        meta: dict[str, float | str | int] = {}
        repo = ctx.reputation_repo
        if repo is not None:
            record = await repo.get(ctx.fingerprint)  # type: ignore[union-attr]
            if record is not None:
                value = max(0.0, min(1.0, record.score / 100.0))
                meta = {
                    "prior_score": record.score,
                    "prior_operator": record.operator_id,
                    "signal_count": record.signal_count,
                }
        return SignalResult(
            name=self.name, value=value, weight=self.weight, meta=meta
        )
