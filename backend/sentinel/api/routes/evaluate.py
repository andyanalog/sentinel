import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from sentinel.api.dependencies import authenticate, get_container
from sentinel.container import Container
from sentinel.core import fingerprint as fp
from sentinel.core.decision import decide
from sentinel.core.signals.base import SignalContext
from sentinel.models.evaluation import EvaluationRequest, EvaluationResult
from sentinel.models.operator import Operator
from sentinel.models.reputation import ReputationSignal
from sentinel.observability import EvalEvent
from sentinel.payments.pool import InsufficientFundsError

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/v1", tags=["evaluate"])


@router.post("/evaluate", response_model=EvaluationResult)
async def evaluate(
    req: EvaluationRequest,
    operator: Operator = Depends(authenticate),
    container: Container = Depends(get_container),
) -> EvaluationResult:
    try:
        await container.pool.debit_evaluation(operator.id)
    except InsufficientFundsError as e:
        # x402-style Payment Required: tell the client where to deposit USDC
        # and which operator_id (as bytes32) the pool contract indexes them by.
        # The adapter exposes these only when a real onchain pool is wired;
        # dummy mode keeps the legacy shape.
        from sentinel.payments.circle import (
            CirclePayments,
            _operator_id_to_bytes32,
        )

        detail: dict[str, object] = {
            "error": "operator_pool_empty",
            "balance": e.balance,
            "eval_cost_usdc": container.settings.eval_cost_usdc,
        }
        if isinstance(container.payments, CirclePayments):
            detail["payment"] = {
                "chain_id": container.settings.arc_chain_id,
                "pool_address": container.payments.pool_address,
                "usdc_address": container.payments.usdc_address,
                "operator_id_bytes32": "0x"
                + _operator_id_to_bytes32(operator.id).hex(),
                "call": "OperatorPool.deposit(operator_id_bytes32, amount)",
            }
        else:
            detail["refill_url"] = f"/v1/operators/{operator.id}/credit"
        raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, detail=detail) from e

    req.operator_id = operator.id
    eval_id = f"ev_{uuid.uuid4().hex[:16]}"
    fingerprint = fp.extract(req)

    ctx = SignalContext(
        fingerprint=fingerprint,
        reputation_repo=container.repo,
        counters=container.counters,
    )
    score, signals = await container.scorer.score(req, ctx)
    action = decide(score)

    # Write signal back so future evals (same app or others) can see it.
    await container.repo.write_signal(
        ReputationSignal(
            fingerprint=fingerprint,
            score=score,
            operator_id=operator.id,
            eval_id=eval_id,
        )
    )

    result = EvaluationResult(
        action=action,
        score=score,
        signals={s.name: round(s.value, 3) for s in signals},
        fingerprint=fingerprint,
        eval_id=eval_id,
    )
    container.feed.record(
        EvalEvent(
            eval_id=eval_id,
            operator_id=operator.id,
            action=action.value,
            score=score,
            fingerprint=fingerprint,
            signals={s.name: round(s.value, 3) for s in signals},
        )
    )
    logger.info(
        "evaluate",
        eval_id=eval_id,
        operator=operator.id,
        fingerprint=fingerprint,
        score=score,
        action=action.value,
    )
    return result
