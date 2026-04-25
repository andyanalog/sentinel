from dataclasses import dataclass
from typing import Any

from sentinel.config import Settings
from sentinel.core.counters import Counters
from sentinel.core.scorer import Scorer
from sentinel.core.signals import (
    CadenceSignal,
    EndpointDiversitySignal,
    ErrorRateSignal,
    IpAsnSignal,
    ReputationSignal,
)
from sentinel.db.session import make_engine, make_session_factory
from sentinel.observability import EvalFeed
from sentinel.payments.pool import PoolManager
from sentinel.reputation.repository import ReputationRepository
from sentinel.workers.ledger_batch import LedgerBatchWorker
from sentinel.workers.pool_debit import PoolDebitWorker


@dataclass
class Container:
    settings: Settings
    cache: Any
    store: Any
    ledger: Any
    payments: Any
    repo: ReputationRepository
    pool: PoolManager
    scorer: Scorer
    counters: Counters
    batch_worker: LedgerBatchWorker
    debit_worker: PoolDebitWorker
    operators: Any  # OperatorRegistry
    feed: EvalFeed


def _build_payments(settings: Settings) -> Any:
    """Real CirclePayments when fully configured, DummyPayments otherwise.

    Same kill-switch logic as _build_ledger: a broken chain config at startup
    must not take the evaluation path down.
    """
    from sentinel.payments.dummy import DummyPayments

    missing = [
        name for name, val in (
            ("ARC_RPC_URL", settings.arc_rpc_url),
            ("OPERATOR_POOL_ADDRESS", settings.operator_pool_address),
            ("ARC_USDC_ADDRESS", settings.arc_usdc_address),
            ("SENTINEL_WALLET_PRIVATE_KEY", settings.sentinel_wallet_private_key),
        ) if not val
    ]
    if missing:
        import structlog
        structlog.get_logger(__name__).warning(
            "circle_payments.disabled_falling_back_to_dummy", missing=missing
        )
        return DummyPayments()

    from sentinel.payments.circle import CirclePayments
    return CirclePayments.from_rpc(
        rpc_url=settings.arc_rpc_url,
        pool_address=settings.operator_pool_address,
        usdc_address=settings.arc_usdc_address,
        private_key=settings.sentinel_wallet_private_key,
        chain_id=settings.arc_chain_id,
    )


def _build_ledger(settings: Settings) -> Any:
    """Real ArcLedger when fully configured, DummyLedger otherwise.

    Kill-switch: if any of rpc_url / contract_address / private_key is
    missing, we fall back silently to the dummy. A broken RPC at startup
    should not take down the evaluation path — a warning is logged and
    the batch worker keeps cycling against the in-process stand-in.
    """
    from sentinel.reputation.dummy import DummyLedger

    missing = [
        name for name, val in (
            ("ARC_RPC_URL", settings.arc_rpc_url),
            ("REPUTATION_LEDGER_ADDRESS", settings.reputation_ledger_address),
            ("SENTINEL_WALLET_PRIVATE_KEY", settings.sentinel_wallet_private_key),
        ) if not val
    ]
    if missing:
        import structlog
        structlog.get_logger(__name__).warning(
            "arc_ledger.disabled_falling_back_to_dummy", missing=missing
        )
        return DummyLedger()

    from sentinel.reputation.ledger import ArcLedger
    return ArcLedger.from_rpc(
        rpc_url=settings.arc_rpc_url,
        contract_address=settings.reputation_ledger_address,
        private_key=settings.sentinel_wallet_private_key,
        chain_id=settings.arc_chain_id,
    )


def build_container(settings: Settings) -> Container:
    from sentinel.api.operators_registry import OperatorRegistry

    if settings.dummy_mode:
        from sentinel.payments.dummy import DummyPayments
        from sentinel.reputation.dummy import DummyCache, DummyLedger, DummyStore

        cache: Any = DummyCache()
        store: Any = DummyStore()
        ledger: Any = DummyLedger()
        payments: Any = DummyPayments()
        operators: Any = OperatorRegistry.in_memory()
    else:
        from sentinel.reputation.cache import RedisCache
        from sentinel.reputation.store import PostgresStore

        engine = make_engine(settings.database_url)
        session_factory = make_session_factory(engine)
        cache = RedisCache(settings.redis_url)
        store = PostgresStore(session_factory)
        ledger = _build_ledger(settings)
        payments = _build_payments(settings)
        operators = OperatorRegistry.postgres(session_factory)

    repo = ReputationRepository(cache, store, ledger)
    pool = PoolManager(payments, settings.eval_cost_usdc)
    scorer = Scorer(
        [
            IpAsnSignal(),
            CadenceSignal(),
            EndpointDiversitySignal(),
            ErrorRateSignal(),
            ReputationSignal(),
        ]
    )
    if settings.dummy_mode:
        counters: Any = Counters()
    else:
        from sentinel.core.counters_redis import RedisCounters

        counters = RedisCounters.from_url(settings.redis_url)
    batch_worker = LedgerBatchWorker(
        ledger,
        settings.ledger_batch_interval,
        settings.ledger_batch_size,
    )
    debit_worker = PoolDebitWorker(payments, settings.pool_debit_interval)
    return Container(
        settings=settings,
        cache=cache,
        store=store,
        ledger=ledger,
        payments=payments,
        repo=repo,
        pool=pool,
        scorer=scorer,
        counters=counters,
        batch_worker=batch_worker,
        debit_worker=debit_worker,
        operators=operators,
        feed=EvalFeed(),
    )
