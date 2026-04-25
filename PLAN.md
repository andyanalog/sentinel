# Sentinel — Trust-as-a-Service API
## Project Build Plan for Claude Code

---

## 1. What We're Building

A middleware trust evaluation service that any API can call per-request to receive a real-time allow/block signal. Operators pay per evaluation via Circle Nanopayments on Arc L1. Behavioral reputation accumulates onchain across every integrated app, creating a cross-network deterrent that improves with scale.

**The user is invisible to the entire system. The operator gets protection. The service earns per-call nano-revenue.**

### Core value props
- Pay-per-call (no monthly fee, scales to zero for small apps)
- Cross-app reputation (bad actor flagged on one API = flagged everywhere)
- Crypto-native payment rail (Circle USDC + Arc L1)
- One-liner SDK integration for Express / Fastify / Hono

### What it is (and what it isn't)

**What it does.** On every request that hits an integrated API, Sentinel derives a *fingerprint* (hash of IP + ASN + user-agent + selected headers) and a *score* (0–100) from behavioral signals — cadence, endpoint diversity, error rate, IP reputation, and cross-operator history. That score maps to `ALLOW` / `CHALLENGE` / `BLOCK`. Reputation lives across three tiers: Redis (hot, last few minutes for burst detection), Postgres (warm, recent aggregated samples), and the Arc L1 `ReputationLedger` contract (cold, durable EMA of 70% prior + 30% new, written in batches — never per request). When another operator later evaluates the same fingerprint, the onchain prior is read back as the heaviest signal (`reputation`, weight 1.5) — that's the mechanism behind the cross-app deterrent.

**What it is not.**
- **Not a data store for request contents.** No payloads, no headers, no PII go onchain — only fingerprint hashes and numeric scores.
- **Not an identity / KYC system.** It never observes the logged-in user and intentionally excludes cookies and bearer tokens from the fingerprint so it survives logout and catches shared credentials.
- **Not a WAF or DDoS edge.** It sits behind your CDN/edge layer and consumes per-request CPU/IO; put Cloudflare, Fastly, etc. in front of it.
- **Not a CAPTCHA on its own.** `CHALLENGE` is a hint — the operator's app decides whether to route to a captcha, email verification, step-up auth, or a slow path.
- **Not deterministic.** Two identical requests can score differently as cross-operator reputation evolves. That's the design: the ledger is a living signal, not a static rule set.

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   Operator's API                    │
│   app.use(sentinel.middleware())                    │
└─────────────────┬───────────────────────────────────┘
                  │ HTTP < 50ms
┌─────────────────▼───────────────────────────────────┐
│              Evaluation Engine (FastAPI)            │
│  1. Extract fingerprint from request                │
│  2. Query reputation (Redis → Postgres → Arc)       │
│  3. Apply operator rules                            │
│  4. Score → ALLOW / CHALLENGE / BLOCK               │
│  5. Debit nanopayment from operator pool            │
│  6. Async: write signal to reputation ledger        │
└──────┬──────────────────────────┬───────────────────┘
       │                          │
┌──────▼──────┐          ┌────────▼────────┐
│  Reputation │          │  Circle         │
│  Ledger     │          │  Nanopayments   │
│  (Arc L1)   │          │  (Arc L1)       │
│             │          │                 │
│  hashed IDs │          │  operator pool  │
│  + scores   │          │  per-eval debit │
└─────────────┘          └─────────────────┘

Reputation layer:
  Hot   → Redis       < 1ms   last 1h signals
  Warm  → PostgreSQL  < 5ms   last 30d history
  Cold  → Arc L1      < 100ms permanent cross-app record
```

---

## 3. Project Directory

```
sentinel/
│
├── PLAN.md                        # This file
├── README.md
├── docker-compose.yml             # Local dev: api, redis, postgres
├── .env.example
├── .gitignore
│
├── contracts/                     # Vyper smart contracts (Arc L1)
│   ├── ReputationLedger.vy        # Hashed fingerprint + score storage
│   ├── OperatorPool.vy            # USDC pool deposit + per-eval debit
│   ├── tests/
│   │   ├── test_reputation.py
│   │   └── test_operator_pool.py
│   └── deploy/
│       └── deploy.py              # Arc deployment script
│
├── backend/                       # FastAPI evaluation engine
│   ├── pyproject.toml
│   ├── pytest.ini
│   │
│   ├── sentinel/
│   │   ├── __init__.py
│   │   ├── main.py                # FastAPI app, lifespan, router registration
│   │   ├── config.py              # Settings via pydantic-settings
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── evaluate.py    # POST /v1/evaluate
│   │   │   │   ├── operators.py   # POST /v1/operators, GET /v1/operators/{id}
│   │   │   │   └── health.py      # GET /health
│   │   │   └── dependencies.py    # Shared FastAPI deps (auth, rate limit)
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── fingerprint.py     # Extract fingerprint from raw request
│   │   │   ├── scorer.py          # Signal aggregation → trust score 0-100
│   │   │   ├── signals/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py        # BaseSignal abstract class
│   │   │   │   ├── ip.py          # IP / ASN signal
│   │   │   │   ├── cadence.py     # Request timing + burst pattern
│   │   │   │   ├── endpoint.py    # Endpoint diversity signal
│   │   │   │   ├── error_rate.py  # 4xx/5xx ratio signal
│   │   │   │   └── reputation.py  # Cross-app ledger signal
│   │   │   └── decision.py        # Score → ALLOW / CHALLENGE / BLOCK
│   │   │
│   │   ├── reputation/
│   │   │   ├── __init__.py
│   │   │   ├── repository.py      # Read/write across hot/warm/cold layers
│   │   │   ├── cache.py           # Redis hot layer
│   │   │   ├── store.py           # Postgres warm layer
│   │   │   └── ledger.py          # Arc contract writer (batched)
│   │   │
│   │   ├── payments/
│   │   │   ├── __init__.py
│   │   │   ├── circle.py          # Circle Nanopayments + Wallets client
│   │   │   └── pool.py            # Operator pool balance management
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── evaluation.py      # EvaluationRequest, EvaluationResult
│   │   │   ├── operator.py        # Operator, OperatorPool
│   │   │   └── reputation.py      # FingerprintRecord, ReputationSignal
│   │   │
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── session.py         # Async SQLAlchemy engine + session
│   │   │   └── migrations/        # Alembic
│   │   │       └── versions/
│   │   │
│   │   └── workers/
│   │       ├── __init__.py
│   │       └── ledger_batch.py    # Async worker: batch writes to Arc
│   │
│   └── tests/
│       ├── conftest.py
│       ├── unit/
│       │   ├── test_fingerprint.py
│       │   ├── test_scorer.py
│       │   └── signals/
│       │       ├── test_cadence.py
│       │       └── test_reputation.py
│       ├── integration/
│       │   ├── test_evaluate_endpoint.py
│       │   └── test_reputation_repository.py
│       └── api/
│           └── test_operators_endpoint.py
│
├── sdk/                           # TypeScript npm package
│   ├── package.json
│   ├── tsconfig.json
│   ├── vitest.config.ts
│   │
│   ├── src/
│   │   ├── index.ts               # Public exports
│   │   ├── client.ts              # HTTP client to evaluation engine
│   │   ├── middleware/
│   │   │   ├── express.ts         # Express middleware
│   │   │   ├── fastify.ts         # Fastify plugin
│   │   │   └── hono.ts            # Hono middleware
│   │   ├── fingerprint.ts         # Client-side request normalization
│   │   └── types.ts               # Shared types (EvalRequest, TrustResult)
│   │
│   └── tests/
│       ├── middleware.express.test.ts
│       └── client.test.ts
│
└── demo/                          # Hackathon demo app
    ├── package.json
    ├── index.ts                   # Simple Express API with SDK integrated
    ├── bot.ts                     # Bot simulator (burst requests)
    └── README.md                  # How to run the demo
```

---

## 4. Contracts

### ReputationLedger.vy
Stores hashed fingerprints with severity scores. Written to in batches by the backend worker.

```
interface:
  write_batch(records: DynArray[Record, 100])  # operator only
  get_score(fingerprint: bytes32) -> uint8
  get_record(fingerprint: bytes32) -> Record

struct Record:
  fingerprint: bytes32    # keccak256(ip + asn + tls_ja3)
  score: uint8            # 0-100
  reported_by: address    # operator contract address
  timestamp: uint256
```

### OperatorPool.vy
Holds USDC deposits per operator. Debited per evaluation call by the backend.

```
interface:
  deposit(operator_id: bytes32, amount: uint256)
  debit(operator_id: bytes32, amount: uint256)  # sentinel service only
  withdraw(operator_id: bytes32, amount: uint256)
  balance(operator_id: bytes32) -> uint256
```

**Deployment**: Both contracts deployed on Arc testnet. Addresses stored in `.env`.

---

## 5. Backend — Key Implementation Details

### 5.1 Evaluation endpoint

```
POST /v1/evaluate
Authorization: Bearer <operator_api_key>

{
  "ip": "1.2.3.4",
  "user_agent": "...",
  "path": "/api/submit",
  "method": "POST",
  "headers": { ... },
  "timestamp": "2026-04-18T12:00:00Z"
}

→ 200 OK
{
  "action": "BLOCK",          # ALLOW | CHALLENGE | BLOCK
  "score": 87,                # 0-100, higher = more suspicious
  "signals": {                # which signals fired
    "burst_pattern": 0.9,
    "cross_app_reputation": 0.8,
    "ip_asn": 0.4
  },
  "fingerprint": "0xabc...",  # hashed, safe to log
  "eval_id": "ev_xxxx"        # idempotency key
}
```

### 5.2 Signal architecture

Each signal is an independent, testable unit:

```python
# core/signals/base.py
from abc import ABC, abstractmethod
from sentinel.models.evaluation import EvaluationRequest, SignalResult

class BaseSignal(ABC):
    weight: float  # contribution to final score

    @abstractmethod
    async def evaluate(self, req: EvaluationRequest) -> SignalResult:
        ...
```

Scorer aggregates all signals with weighted average. Adding a new signal = new file + register in scorer. No other changes needed.

### 5.3 Reputation repository pattern

```python
# reputation/repository.py
class ReputationRepository:
    def __init__(self, cache: RedisCache, store: PostgresStore, ledger: ArcLedger):
        self._cache = cache
        self._store = store
        self._ledger = ledger

    async def get(self, fingerprint: str) -> ReputationRecord | None:
        # hot → warm → cold, write-through on miss
        if record := await self._cache.get(fingerprint):
            return record
        if record := await self._store.get(fingerprint):
            await self._cache.set(fingerprint, record)
            return record
        return await self._ledger.get(fingerprint)

    async def write_signal(self, fingerprint: str, score: int, operator_id: str):
        # always write to hot + warm immediately
        # cold (Arc) written via batched worker
        await self._cache.set(fingerprint, score)
        await self._store.upsert(fingerprint, score, operator_id)
        await self._batch_queue.enqueue(fingerprint, score, operator_id)
```

### 5.4 Nanopayment per evaluation

Every evaluation call debits the operator's pool. Handled async so it never adds latency to the evaluation response:

```python
# payments/pool.py
async def debit_evaluation(operator_id: str, eval_id: str):
    # $0.0001 USDC per evaluation
    # via Circle Nanopayments — off-chain accumulation
    # settled onchain periodically by Circle
    ...
```

If operator pool balance is zero, return 402 Payment Required with a refill URL. Never silently allow without payment.

### 5.5 Code standards

- **Python 3.12**, PEP 8, type hints everywhere
- **Pydantic v2** for all models and settings
- **async throughout** — no blocking calls on the event loop
- **Dependency injection** via FastAPI `Depends()` for all repositories and clients
- **Repository pattern** — no raw DB queries outside repository classes
- **No business logic in route handlers** — routes call services, services call repositories
- **Environment config** via `pydantic-settings`, never hardcoded
- **Structured logging** via `structlog`, every evaluation logged with `eval_id`
- **All Circle API interactions via Circle MCP**

---

## 6. SDK — Key Implementation Details

### 6.1 Express middleware (primary target)

```typescript
// One-liner integration
app.use(sentinel.middleware())

// Per-route with overrides
app.post('/expensive', sentinel.evaluate({ costWeight: 2.0 }), handler)
```

### 6.2 What the middleware does

1. Extract request metadata (ip, ua, path, method, headers)
2. POST to evaluation engine with operator API key
3. If `action === 'BLOCK'` → return 429 before handler runs
4. If `action === 'ALLOW'` → call `next()`
5. Attach `req.sentinel` with score and signals for optional logging

### 6.3 Code standards

- **TypeScript strict mode**
- **Zero runtime dependencies** in the core SDK (fetch only)
- Framework adapters (express, fastify, hono) as optional peer deps
- Full type exports — operators get autocomplete on everything
- **Vitest** for all tests

---

## 7. Testing Strategy

| Layer | Tool | Target coverage |
|---|---|---|
| Unit (signals, scorer, fingerprint) | pytest | 90% |
| Integration (API + Redis + Postgres) | pytest + testcontainers | 80% |
| Contract (Vyper) | pytest + ape | all public functions |
| SDK unit | Vitest | 85% |
| SDK middleware | Vitest + supertest | all middleware paths |
| E2E demo | manual + bot script | demo script passes |

---

## 8. Environment Variables

```bash
# Arc
ARC_RPC_URL=
ARC_CHAIN_ID=
REPUTATION_LEDGER_ADDRESS=
OPERATOR_POOL_ADDRESS=
SENTINEL_WALLET_PRIVATE_KEY=

# Circle (via Circle MCP)
CIRCLE_API_KEY=
CIRCLE_WALLET_SET_ID=

# Database
DATABASE_URL=postgresql+asyncpg://sentinel:sentinel@localhost:5432/sentinel
REDIS_URL=redis://localhost:6379/0

# Service
SENTINEL_API_SECRET=          # internal secret for SDK auth
EVAL_COST_USDC=0.0001         # per-evaluation charge
LEDGER_BATCH_SIZE=100         # fingerprints per onchain write
LEDGER_BATCH_INTERVAL=60      # seconds between batch writes
```

---

## 9. Hackathon Demo Script

**Goal**: show 50+ onchain transactions, live blocking, and cross-app reputation kick-in.

1. Start all services via `docker-compose up`
2. Deploy contracts to Arc testnet (`python contracts/deploy/deploy.py`)
3. Register two demo operators (App A, App B) via API
4. Start demo App A (`cd demo && npx ts-node index.ts`)
5. Run bot simulator against App A (`npx ts-node bot.ts --target=A --rps=20`)
6. Show live dashboard: trust scores degrading, blocks firing, nanopayments depleting pool
7. Show Arc explorer: reputation ledger updating onchain
8. Start demo App B (fresh, no history)
9. Run same bot against App B — **blocked on first request** via cross-app reputation
10. Show App B's operator pool: charged for the single evaluation that caught the bot

**The money shot**: step 9. App B has never seen this fingerprint. The ledger has. That's the product.

---

## 9b. Dummy Mode

The entire service runs without any external dependencies via `--dummy` flag. No Arc node, no Circle API, no Redis, no Postgres required. Useful for local development, CI, and hackathon demos where environment setup is a risk.

### How to activate

```bash
# Backend
uvicorn sentinel.main:app --dummy

# Demo app
npx ts-node demo/index.ts --dummy

# Bot simulator (always works regardless of mode)
npx ts-node demo/bot.ts --target=http://localhost:8000 --rps=20
```

### What changes in dummy mode

| Component | Normal | Dummy |
|---|---|---|
| Redis | Required | In-process dict, resets on restart |
| PostgreSQL | Required | In-memory SQLite via aiosqlite |
| Arc contract | Required | `DummyLedger` — logs writes to stdout |
| Circle Nanopayments | Required | `DummyPayments` — logs debits, never fails |
| Operator auth | API key required | Any string accepted as valid key |
| Pool balance | Onchain | Starts at $100 fake USDC, never empties |

### Implementation

Each external adapter has a dummy counterpart behind the same interface. The real and dummy implementations are swapped at startup via dependency injection — no `if dummy:` branches in business logic.

```python
# config.py
class Settings(BaseSettings):
    dummy_mode: bool = False  # set via --dummy flag or SENTINEL_DUMMY=true

# main.py — lifespan selects adapters based on settings
def build_container(settings: Settings) -> Container:
    if settings.dummy_mode:
        return Container(
            cache=DummyCache(),
            store=DummyStore(),
            ledger=DummyLedger(),
            payments=DummyPayments(),
        )
    return Container(
        cache=RedisCache(settings.redis_url),
        store=PostgresStore(settings.database_url),
        ledger=ArcLedger(settings.arc_rpc_url, ...),
        payments=CirclePayments(settings.circle_api_key),
    )
```

```python
# reputation/dummy.py
class DummyLedger:
    """Simulates Arc reputation ledger in-process."""
    def __init__(self):
        self._store: dict[str, int] = {}

    async def get_score(self, fingerprint: str) -> int | None:
        return self._store.get(fingerprint)

    async def write_batch(self, records: list[ReputationRecord]):
        for r in records:
            self._store[r.fingerprint] = r.score
        logger.info("dummy_ledger.write_batch", count=len(records))

# payments/dummy.py
class DummyPayments:
    """Simulates Circle Nanopayments in-process."""
    def __init__(self):
        self._pools: dict[str, float] = defaultdict(lambda: 100.0)

    async def debit(self, operator_id: str, amount: float):
        self._pools[operator_id] -= amount
        logger.info("dummy_payments.debit", operator=operator_id,
                    amount=amount, balance=self._pools[operator_id])
```

### Dummy mode behavior to preserve realism

- Signal scoring runs **exactly the same logic** as production — no shortcuts
- Burst detection and cadence signals work correctly (in-memory counters)
- Cross-app reputation **persists across requests within a session** — so the demo script still shows a bot getting flagged, scores degrading, and cross-app blocking working
- Ledger writes are **logged as if they were onchain** with a fake tx hash (`0xdummy_<uuid>`)
- Nanopayment debits are **logged with running balance** so the operator pool drain is visible

### Dummy mode in tests

```python
# conftest.py
@pytest.fixture
def dummy_settings():
    return Settings(dummy_mode=True)

@pytest.fixture
async def app(dummy_settings):
    container = build_container(dummy_settings)
    return create_app(container)
```

All integration tests run in dummy mode by default. Real-adapter tests are marked `@pytest.mark.integration` and skipped in CI unless env vars are present.

---

## 10. Build Order

Start here, in this order:

1. `docker-compose.yml` — postgres + redis + api skeleton
2. `backend/sentinel/config.py` — settings, env loading
3. `backend/sentinel/db/` — SQLAlchemy setup + first migration
4. `backend/sentinel/models/` — all Pydantic models
5. `backend/sentinel/core/fingerprint.py` — extract from raw request
6. `backend/sentinel/core/signals/` — ip, cadence, error_rate (skip reputation signal first)
7. `backend/sentinel/core/scorer.py` + `decision.py`
8. `backend/sentinel/reputation/` — cache + store only (skip Arc ledger first)
9. `backend/sentinel/api/routes/evaluate.py` — wire it all together, get a working response
10. `backend/tests/` — unit + integration tests to this point
11. `sdk/src/` — TypeScript client + Express middleware
12. `demo/` — demo app + bot simulator
13. `contracts/` — Vyper contracts + deploy script
14. `backend/sentinel/reputation/ledger.py` + `workers/ledger_batch.py` — Arc integration
15. `backend/sentinel/payments/` — Circle Nanopayments integration via Circle MCP
16. End-to-end demo run + fix

---

## 11. What to Defer (post-hackathon)

- CHALLENGE action (currently just ALLOW or BLOCK)
- Operator dashboard UI
- Dispute / appeal window for false positives
- Quorum-based slash conditions
- SDK adapters for Fastify and Hono
- Webhook callbacks on block events
- Tiered pricing per operator plan
