# Sentinel — Trust-as-a-Service for APIs

One line of middleware. Every request scored in real time as **ALLOW**, **CHALLENGE**, or **BLOCK**. Reputation written onchain so it's verifiable and portable across every integrated app.

## Live demo

| | URL |
|---|---|
| Visual demo (try it) | https://demo-production-ccb5.up.railway.app/ |
| Backend API | https://sentinel-demo.up.railway.app/ |
| `ReputationLedger` on Arc testnet | [`0x92292B00…`](https://testnet.arcscan.app/address/0x92292B00e76Bf8022b15D79CC8F85766cCA289A0?tab=index) |
| `OperatorPool` on Arc testnet | [`0x10504B3F…`](https://testnet.arcscan.app/address/0x10504B3F4B5f172a88C34570Ab8E91aEb3bD9B63?tab=index) |

Click "Send normal request" to score legitimate traffic; click "Simulate bot attack" to fire 30 req/s for 10 s and watch the verdict flip ALLOW → CHALLENGE → BLOCK in real time. The "View on chain" button opens the contract that stores fingerprints we've evaluated.

## Stack

**Backend** — Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 (async), Alembic, structlog. Postgres for warm storage, Redis for hot counters. Run via uvicorn or Docker.

**SDK** — TypeScript, distributed as a `file:` workspace dep. Adapters for Express, Fastify, and Hono. One async middleware that calls `/v1/evaluate` per request and short-circuits 429 on BLOCK.

**Demo app** — Express + tsx, single-page UI with Server-Sent Events for the live decision feed. Self-contained "bot loop" that fires synthetic traffic so judges don't need a shell to trigger an attack.

**Smart contracts** — Vyper, deployed with Ape framework on Arc L1 testnet:

- `ReputationLedger` — `write_batch(records[])` writes batched fingerprint scores (one tx per N evals). Public reads via `get_record(fingerprint)`.
- `OperatorPool` — `deposit(operator_id, amount)` for funding, `debit(operator_id, amount)` for per-eval billing in USDC.

**Payments** — **Circle USDC** on Arc L1 (USDC contract `0x36000000…`). Settlement model = **Circle Nanopayments / x402 / Gateway** style: each evaluation debits a fraction of a cent from the operator's pool balance; debits are batched onchain so gas stays bounded. No invoices, no monthly minimum — the contract balance is the bill.

**Chain** — Arc L1 testnet (chain ID `5042002`, RPC `https://rpc.testnet.arc.network`). web3.py + eth_account for tx signing inside the backend; the operator wallet is funded via faucet for gas.

**Hosting** — Railway (backend, demo, Postgres, Redis). Vercel for frontend.

## Quickstart — local, dummy mode (no chain, no DB)

The fastest way to see Sentinel work end-to-end. Dummy mode swaps in in-memory adapters for cache, store, ledger, and payments — no Postgres, no Redis, no testnet wallet.

```bash
# 1. Backend
cd backend
pip install -e .
SENTINEL_DUMMY=true uvicorn sentinel.main:app --reload --port 8000

# 2. Demo app (separate terminal)
cd demo && npm install
SENTINEL_ENDPOINT=http://localhost:8000 npx tsx index.ts
```

Open `http://localhost:3000`, click around. Backend health: `curl localhost:8000/health` → `{"status":"ok","dummy_mode":true}`.

## Quickstart — local, full mode (Postgres + Redis)

```bash
docker-compose up -d postgres redis     # bring up sibling stores
cd backend
cp .env.example .env                    # fill in Arc + wallet vars (see below)
alembic upgrade head                    # create tables
uvicorn sentinel.main:app --port 8000   # SENTINEL_DUMMY unset → real adapters
```

Required `backend/.env` keys for full mode (already populated from Arc testnet deploy):

```
DATABASE_URL=postgresql+asyncpg://sentinel:sentinel@localhost:5432/sentinel
REDIS_URL=redis://localhost:6379/0
ARC_RPC_URL=https://rpc.testnet.arc.network
ARC_CHAIN_ID=5042002
REPUTATION_LEDGER_ADDRESS=0x92292B00e76Bf8022b15D79CC8F85766cCA289A0
OPERATOR_POOL_ADDRESS=0x10504B3F4B5f172a88C34570Ab8E91aEb3bD9B63
ARC_USDC_ADDRESS=0x3600000000000000000000000000000000000000
SENTINEL_WALLET_PRIVATE_KEY=…           # service wallet, testnet only
```

## End-to-end testing on real testnet

Three scripts under `backend/scripts/` exercise the full Arc-side pipeline. All assume `.secrets/testnet_deployment.json` and `.secrets/sentinel_service_key.json` exist (created by `deploy_testnet.py`).

```bash
cd backend
export SSL_CERT_FILE=$(python -c "import certifi; print(certifi.where())")
export PYTHONPATH=.

# 1. Single end-to-end loop: card → pool credit → 20 evals → flush → balance check
#    Proves CirclePayments + PoolManager work against the live OperatorPool.
python scripts/testnet_e2e_demo.py

# 2. Seed N rounds of OperatorPool activity (one deposit + one batched debit per round)
#    Default 25 rounds = ~50 onchain txs. Useful for populating the contract before judging.
python scripts/seed_chain.py 25

# 3. Seed N batched fingerprint writes to ReputationLedger
#    Default 30 rounds × 3 signals each = 30 write_batch txs (90 fingerprints).
python scripts/seed_ledger.py 50 3
```

After running, the contracts will show fresh activity at the explorer URLs in the table above.

To replay end-to-end **through the deployed backend** (so a real `/api/submit` from the demo writes to chain):

```bash
# unset SENTINEL_DUMMY, start backend, fire requests
unset SENTINEL_DUMMY
uvicorn sentinel.main:app --port 8000 &
curl -X POST localhost:8000/v1/operators -H content-type:application/json -d '{"name":"e2e"}'
# response gives you {operator: {api_key: "sk_..."}, pool: {...}}
# fund the pool, then submit through the SDK:
SENTINEL_ENDPOINT=http://localhost:8000 SENTINEL_API_KEY=sk_... npx tsx demo/index.ts
```

The `LedgerBatchWorker` flushes accumulated signals every `LEDGER_BATCH_INTERVAL` seconds; the `PoolDebitWorker` settles debits every `POOL_DEBIT_INTERVAL` seconds. Default 60s / 30s — drop to ~10s during demos.

## What it does

On every request hitting your API, Sentinel derives a **fingerprint** (a hash of IP + ASN + user-agent + selected headers) and a **score** (0–100) from five behavioral signals — request cadence, endpoint diversity, error rate, IP reputation, and cross-operator history.

The score maps to `ALLOW` (<40) / `CHALLENGE` (40–54) / `BLOCK` (≥55). The fingerprint's running reputation is stored across three tiers:

- **Hot** — Redis, per-fingerprint counters and short-lived score cache.
- **Warm** — Postgres, recent fingerprint records with EMA-smoothed scores (70% prior + 30% new).
- **Cold** — Arc L1 `ReputationLedger`, batched onchain writes for durable, cross-operator state.

When a different operator later evaluates the same fingerprint, the onchain prior is read back as the heaviest signal (`reputation`, weight 1.5). That's the mechanism behind "flagged on one API = flagged everywhere."

## What it is not

- It does **not** store payloads, headers, or PII onchain — only fingerprint hashes and numeric scores.
- It is **not** an identity / KYC system; it never sees the logged-in user and excludes cookies / bearer tokens from the fingerprint so it survives logout and catches shared credentials.
- It is **not** a WAF or DDoS edge — put it behind Cloudflare, not in front of it.
- It is **not** a CAPTCHA replacement; `CHALLENGE` is a hint that *your* app should route to a captcha, email verification, or slow path.
- It is **not** a deterministic rule engine — two identical requests can score differently as cross-operator reputation evolves, which is the point.

## Core value props

- **Pay-per-call.** No monthly seat fee, no minimum. Scales to zero for a side project; scales linearly under a credential-stuffing spike. Settled in USDC via Circle Nanopayments so a $9/mo floor never blocks integration.
- **Blockchain abstracted from the developer.** You never touch a wallet, a chain ID, or a gas estimator. Top up the operator pool with a card or USDC; per-call debits draw it down. Crypto is how we settle and how reputation becomes portable — not a requirement to use the product.
- **Cross-app reputation.** A fingerprint flagged on one integrated API is flagged on all of them. A solo founder on day one inherits the same signal quality as a funded company a year in.
- **One-liner SDK.** `app.use(sentinel({ apiKey }))` for Express / Fastify / Hono. Returns 429 on BLOCK, attaches `req.sentinel` for CHALLENGE routing.

## A note on rotating IPs

Consumer residential IPs rotate every 24–48 hours, producing a new fingerprint. Real limitation, handled with layered defenses:

- **ASN reputation survives the rotation** — same ISP, same ASN, same coarser prior.
- **Behavioral signals catch the new fingerprint fast** — cadence + endpoint diversity don't need history.
- **Non-IP components are sticky** — UA, accept-language, header ordering tend to persist across rotations from the same device.
- **The system is probabilistic, not a bouncer** — goal is to raise the cost of abuse, not make a perfect decision on request 1.

For sophisticated attackers using residential-proxy networks that rotate per-request, the roadmap adds TLS JA4 fingerprinting and (browser-only) canvas/WebGL signals.

## Real-world scenarios

- **Signup endpoints fighting fake account farms** — sees behavior across signup → first login → first write, not just at the form widget.
- **LLM / AI inference APIs under scraper pressure** — fingerprints across key+IP+ASN+cadence; cross-tenant reputation that Cloudflare Bot Management can't do.
- **Login endpoints defending credential stuffing** — sees the same botnet hitting other login endpoints; blocks on request 1 not request 100.
- **Free-tier abuse on SaaS / dev APIs** — Castle.io / Arkose-class signal at fractions of a cent per call, no enterprise sales cycle.
- **Review / comment / UGC spam** — catches coordinated rings before content-level classifiers run.
- **Crypto faucets, airdrop claims, quest platforms** — onchain product + onchain payment rail + onchain reputation ledger.

## Layout

```
backend/        FastAPI evaluation engine + workers + alembic migrations
  scripts/      testnet seeders + e2e demo (testnet_e2e_demo.py, seed_chain.py, seed_ledger.py)
sdk/            TypeScript SDK (Express / Fastify / Hono adapters)
demo/           Express demo app + visual UI + bot simulator
dashboard/      Operator dashboard (Vite + React)
frontend/       Marketing site (Vite + React)
contracts/      Vyper contracts (ReputationLedger, OperatorPool, MockERC20)
```

## Further reading

- [PLAN.md](./PLAN.md) — full architecture
- [REFERENCE.md](./REFERENCE.md) — SDK + HTTP API reference
- [HOWTO.md](./HOWTO.md) — task-oriented recipes
- [contracts/README.md](./contracts/README.md) — contract addresses + Ape commands
