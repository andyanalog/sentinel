# HOWTO — Manual test walkthrough

End-to-end sanity check of Sentinel in dummy mode. No external services required. Every step tells you exactly what success and failure look like.

Assumes:
- Python backend running on `http://localhost:8000` (started with `SENTINEL_DUMMY=true`)
- Node demo App A running on `http://localhost:3000` (started with `SENTINEL_API_KEY=demo-app-a`)

You don't need App B running for steps 1–5. Start it only for step 6.

---

## 0. Smoke test: is the backend alive?

```bash
curl -s http://localhost:8000/health | jq
```

**Expected (positive):**
```json
{ "status": "ok", "dummy_mode": true }
```

**Wrong:**
- connection refused → backend not running
- `"dummy_mode": false` → you forgot `SENTINEL_DUMMY=true`; stop the backend, re-export, restart

---

## 1. Auth is enforced

```bash
curl -i -s -X POST http://localhost:8000/v1/evaluate \
  -H "content-type: application/json" \
  -d '{"ip":"1.2.3.4"}'
```

**Expected:** `HTTP/1.1 401 Unauthorized` with body `{"detail":"missing bearer token"}`

**Wrong:** 200 OK — auth is broken.

---

## 2. A benign evaluation returns ALLOW

```bash
curl -s -X POST http://localhost:8000/v1/evaluate \
  -H "authorization: Bearer demo-app-a" \
  -H "content-type: application/json" \
  -d '{
    "ip":"127.0.0.1",
    "user_agent":"Mozilla/5.0",
    "path":"/",
    "method":"GET"
  }' | jq
```

**Expected (positive):**
```json
{
  "action": "ALLOW",          // score < 40
  "score": 0,                 // low — private IP, no history
  "signals": {
    "ip_asn": 0,
    "burst_pattern": 0.083,
    "endpoint_diversity": 1,
    "error_rate": 0,
    "cross_app_reputation": 0
  },
  "fingerprint": "0x…",       // 0x + 64 hex chars
  "eval_id": "ev_…"
}
```

What to verify:
- `action` is `ALLOW` (score under 40)
- `fingerprint` starts with `0x` and is 66 chars total
- `eval_id` is unique each call (run it twice to confirm)

**Wrong:**
- `BLOCK` or `CHALLENGE` on a first benign call from `127.0.0.1` — the scorer is mis-weighted
- 500 / 422 — payload mismatch; double-check JSON

---

## 3. The backend logs each evaluation

Watch the backend terminal. After step 2 you should see a line like:

```
evaluate eval_id=ev_… operator=op_… fingerprint=0x… score=0 action=ALLOW
```

Plus — because we're in dummy mode — a payment debit:

```
dummy_payments.debit operator=op_… amount=0.0001 balance=0.9999
```

**Wrong:** no log line → `structlog` not printing, check you didn't redirect stdout.

---

## 4. Bursting from a single fingerprint escalates to BLOCK

Simulate a bot by sending the same payload 30 times fast. This exercises the `burst_pattern` and reputation signals.

```bash
for i in $(seq 1 30); do
  curl -s -X POST http://localhost:8000/v1/evaluate \
    -H "authorization: Bearer demo-app-a" \
    -H "content-type: application/json" \
    -d '{
      "ip":"185.220.1.42",
      "user_agent":"BurstBot/1.0",
      "path":"/api/submit",
      "method":"POST"
    }' | jq -r '"\(.action)\t\(.score)\t\(.signals.burst_pattern)\t\(.signals.cross_app_reputation)"'
done
```

**Expected progression** (BLOCK threshold is 65; ALLOW threshold is 40):
- Request 1:  `ALLOW      ~22   0.07   0.0`   (no prior record; burst window just started)
- Request 5:  `CHALLENGE  ~45   0.33   0.3…`  (ip_asn + ramp-up both contribute)
- Request 15: `CHALLENGE  ~62   1.0    0.6…`  (burst signal saturates here)
- Request 30: `BLOCK      ~70   1.0    0.7…`  (cross-app reputation has converged)

The `burst_pattern` column climbs toward 1.0 and saturates around request 15. `cross_app_reputation` lags by one request (each call writes the signal that the next call reads) and converges via EMA around ~0.7. Score plateaus in the low 70s — that's the new BLOCK zone.

**Wrong:**
- No column ever reaches `BLOCK` → the scorer thresholds in `core/decision.py` were changed, or the window in `CadenceSignal` is too large
- `cross_app_reputation` stays at 0 → the reputation repository isn't writing back; check backend logs for exceptions

---

## 5. The demo Express app wires it up end-to-end

Make sure App A is running on :3000, then:

```bash
# benign request via a real browser-ish UA — should 200
curl -i -s http://localhost:3000/ -H "user-agent: Mozilla/5.0" | head -n 5
```

**Expected:** `HTTP/1.1 200 OK` with a JSON body showing `app`, `score`, `eval_id`.

```bash
# now hammer /api/submit from a "bot" IP via spoofed XFF
for i in $(seq 1 25); do
  curl -i -s -X POST http://localhost:3000/api/submit \
    -H "x-forwarded-for: 185.220.1.42" \
    -H "user-agent: BurstBot/1.0" \
    -H "content-type: application/json" \
    -d '{"x":1}' | head -n 1
done
```

**Expected:** first handful of lines are `HTTP/1.1 200 OK`, then they flip to `HTTP/1.1 429 Too Many Requests`. Once they're 429, they stay 429.

**Note on Express `trust proxy`:** by default Express does NOT trust `X-Forwarded-For`, so `req.ip` will be `::1`/`127.0.0.1` and every bot "IP" looks the same to the middleware. That's actually fine for the demo — the bot's fingerprint is stable regardless, so burst detection still fires. If you want real IP extraction in production, call `app.set("trust proxy", true)` in `demo/index.ts`.

**Wrong:**
- Every request stays 200 → middleware isn't actually running; check that `trust.middleware()` is registered before the route handlers in `demo/index.ts`
- Every request is 429 from request #1 → the fingerprint is already flagged from step 4, which is correct! Wait ~60s (cadence window clears) and retry, or restart the backend to reset the in-memory dummy store

---

## 6. The money shot — cross-app blocking

Start App B in a second shell:

```bash
cd demo
PORT=3001 APP_NAME="App B" SENTINEL_API_KEY=demo-app-b npx tsx index.ts
```

App B is a brand-new operator. It's never seen any traffic.

Now hit App B from the **same bot fingerprint** you already burned in step 5:

```bash
curl -i -s -X POST http://localhost:3001/api/submit \
  -H "x-forwarded-for: 185.220.1.42" \
  -H "user-agent: BurstBot/1.0" \
  -H "content-type: application/json" \
  -d '{"x":1}' | head -n 1
```

**Expected (the whole point of the product):** `HTTP/1.1 429 Too Many Requests` on the **first** request. App B has no local history, but the shared reputation ledger flagged this fingerprint during step 5 against App A.

**Wrong:**
- 200 OK → the reputation repository isn't sharing state across operators. That means either:
  1. You restarted the backend between steps 5 and 6 (dummy mode is in-process only)
  2. The fingerprint differs — check that both bot calls use identical `user-agent` and `x-forwarded-for` (Express's `req.ip` is what's sent to Sentinel unless `trust proxy` is on; if it's off, both apps see `::1` and the fingerprint will still match, which is what we want here)

---

## 7. Operator pool lifecycle

```bash
# create a brand-new operator
curl -s -X POST http://localhost:8000/v1/operators \
  -H "content-type: application/json" \
  -d '{"name":"test-shop"}' | jq
```

**Expected:** 201 with `operator.api_key` starting `sk_` and `pool.balance_usdc` = 100.0 (dummy-mode seeds every new operator at $100 fake USDC).

```bash
# check the pool
OP_ID=<id from above>
curl -s http://localhost:8000/v1/operators/$OP_ID | jq
```

**Expected:** `{"operator_id": "op_…", "balance_usdc": 100.0, "total_evaluations": 0}`

```bash
# credit $50
curl -s -X POST http://localhost:8000/v1/operators/$OP_ID/credit \
  -H "content-type: application/json" \
  -d '{"amount_usdc":50}' | jq
```

**Expected:** `"balance_usdc": 150.0`.

Now do ~100 evaluations against this operator. The pool drains by `0.0001` per call. After N calls, balance should be roughly `150 - 0.0001*N`. That's the per-evaluation nanopayment debit in action.

---

## 8. Pool-empty returns 402

Dummy payments start every operator at `$100`. You won't realistically drain it manually. To test the 402 path, create an operator and immediately debit the pool to zero in Python REPL, or just trust the integration test `test_evaluate_blocks_on_burst` — it exercises the happy path; the 402 path is covered by the `PoolManager.debit_evaluation` unit logic.

If you want to force it, temporarily set `EVAL_COST_USDC=200` before launching the backend — the first eval will exceed the $100 seed and you'll see:

```
HTTP/1.1 402 Payment Required
{"detail":{"error":"operator_pool_empty","balance":100.0,"refill_url":"/v1/operators/op_…/credit"}}
```

---

## 9. Run the automated tests (optional but recommended)

```bash
cd backend
pip install -e '.[dev]'
pytest -q
```

**Expected:** all tests pass, ~10 tests across unit + integration. If any fail, read the traceback; the tests pin exactly the behavior described in this guide.

```bash
cd ../sdk
npm install
npm test
```

**Expected:** 5 vitest tests pass (client + express middleware).

---

## Troubleshooting cheat sheet

| Symptom | Likely cause |
|---|---|
| `connection refused` on :8000 | backend not running |
| `401 missing bearer token` | forgot `-H "authorization: Bearer …"` |
| every request is `ALLOW` | reputation repo not writing back (check backend logs for exceptions) |
| every request is `BLOCK` | fingerprint already poisoned from an earlier run — restart the backend |
| `429` from Express but `ALLOW` from Sentinel | another middleware is throwing 429; check the order in `demo/index.ts` |
| demo crashes with `ERR_MODULE_NOT_FOUND @sentinel/sdk` | run `npm install` in `demo/` so the `file:../sdk` link is set up |
| `dummy_mode: false` in `/health` | `SENTINEL_DUMMY=true` was not set when uvicorn started |

---

## Testnet live mode (Phase 5.2)

Runs the full stack — Postgres, Redis, backend — against real Arc testnet contracts, via one `docker compose` command. The dashboard still runs locally (`npm run dev`) against the dockerized backend.

### Prereqs

- Contracts deployed to Arc testnet. You should have `backend/.secrets/testnet_deployment.json` from `scripts/deploy_testnet.py` (Phase 4.0).
- `backend/.env` populated. Copy `/.env.example` and fill in the testnet addresses + service wallet key. Minimum required for non-dummy mode:
  ```
  SENTINEL_DUMMY=false
  SENTINEL_API_SECRET=<any long random string>
  EVAL_COST_USDC=0.0001
  ARC_RPC_URL=https://rpc.testnet.arc.network
  ARC_CHAIN_ID=5042002
  ARC_USDC_ADDRESS=<usdc address on Arc testnet>
  REPUTATION_LEDGER_ADDRESS=<from testnet_deployment.json>
  OPERATOR_POOL_ADDRESS=<from testnet_deployment.json>
  SENTINEL_WALLET_PRIVATE_KEY=0x<service wallet key>
  ```
- Docker Desktop running.

### 1. Bring up the stack

```bash
docker compose up -d --build
docker compose ps
```

**Expected:** three services (`postgres`, `redis`, `api`) all `healthy` / `running`.

### 2. Apply migrations inside the api container

```bash
docker compose exec api alembic upgrade head
```

**Expected:** `Running upgrade -> <rev>, initial`. (Idempotent; safe to re-run.)

### 3. Confirm live mode

```bash
curl -s http://localhost:8000/health | jq
```

**Expected:**
```json
{ "status": "ok", "dummy_mode": false }
```

If `dummy_mode: true` → `SENTINEL_DUMMY` is still `true` in `backend/.env`, or one of the four chain vars (RPC/ledger/pool/key) is missing. The container kill-switch silently falls back to dummy.

### 4. Start the dashboard

```bash
cd dashboard
npm run dev
```

Open http://localhost:5173. The operators table will show registered operators with their **onchain** USDC balance (projected — onchain minus pending debits).

### 5. Credit an operator from the UI

Click **Credit** on an operator row, enter `0.01`. The backend service wallet does `usdc.approve` + `pool.deposit`; within ~2.5s the balance in the table updates.

Verify onchain at `https://testnet.arcscan.app/address/<OPERATOR_POOL_ADDRESS>` — you should see the deposit tx.

### 6. Run evaluations, watch balance drop

```bash
for i in {1..20}; do
  curl -s -X POST http://localhost:8000/v1/evaluate \
    -H "authorization: Bearer <operator api key>" \
    -H "content-type: application/json" \
    -d '{"ip":"127.0.0.1","user_agent":"curl","path":"/","method":"GET"}' > /dev/null
done
```

**During the burst:** dashboard balance ticks down in real time (projected). On-chain balance stays flat — debits are enqueued, not settled.

**After `POOL_DEBIT_INTERVAL` (default 10s):** `PoolDebitWorker` flushes one `OperatorPool.debit` tx per operator. Onchain balance converges to `credited − evals × eval_cost`. One tx on arcscan, not twenty.

### 7. Tear down

```bash
docker compose down           # keeps pgdata volume
docker compose down -v        # also wipes Postgres
```

The service wallet and pool/ledger state on testnet are untouched — only local DB/Redis state resets.
