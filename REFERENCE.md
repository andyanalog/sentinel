# Sentinel — SDK & API Reference

Everything you need to integrate Sentinel into an existing service, call the HTTP API directly, or administer an operator pool. For architecture, trust-scoring internals, and roadmap see [PLAN.md](./PLAN.md).

- **Base URL (dummy / local):** `http://localhost:8000`
- **Authentication:** `Authorization: Bearer <operator_api_key>` on all `/v1/evaluate` calls. Operator management and dashboard endpoints are unauthenticated in dummy mode.
- **Content type:** `application/json`.
- **Latency budget:** evaluation returns in < 50 ms p95 in dummy mode, < 150 ms p95 in full mode. SDKs default to a 1500 ms client-side timeout and fail open on timeout.

---

## Table of contents

1. [Installation](#1-installation)
2. [Quick start (Express)](#2-quick-start-express)
3. [SDK reference](#3-sdk-reference)
   - [`SentinelClient`](#31-sentinelclient)
   - [`sentinel()` factory](#32-sentinel-factory)
   - [Framework adapters](#33-framework-adapters)
   - [Types](#34-types)
   - [Fail-open semantics](#35-fail-open-semantics)
4. [HTTP API reference](#4-http-api-reference)
   - [`POST /v1/evaluate`](#41-post-v1evaluate)
   - [Operator management](#42-operator-management)
   - [Dashboard](#43-dashboard)
   - [Health](#44-health)
5. [Decision semantics](#5-decision-semantics)
6. [Error model](#6-error-model)
7. [Operational notes](#7-operational-notes)

---

## 1. Installation

```bash
# Workspace install (monorepo layout)
npm install @sentinel/sdk

# Or link the local package directly
npm install file:../sdk
```

The package is source-only TypeScript — it ships `.ts` files and is executed with `tsx`, `vite-node`, or your bundler of choice. No build step is required in the consuming app.

**Peer requirements.** Node 18+ (for native `fetch` and `AbortController`). Framework adapters require the corresponding framework as a peer: `express@4+`, `fastify@4+`, or `hono@4+`.

---

## 2. Quick start (Express)

```ts
import express from "express";
import { sentinel } from "@sentinel/sdk";

const app = express();
app.set("trust proxy", true);               // required so req.ip reflects the real client

app.use(
  sentinel({
    apiKey: process.env.SENTINEL_API_KEY!,
    endpoint: "http://localhost:8000",      // optional, this is the default
  }).middleware(),
);

app.post("/signup", (req, res) => {
  if (req.sentinel?.action === "CHALLENGE") {
    // Route to captcha, email verification, or slow-path handler.
    return res.status(202).json({ challenge: "captcha" });
  }
  res.json({ ok: true });
});

app.listen(3000);
```

Behavior:

- `action === "BLOCK"` → middleware responds `429 blocked_by_sentinel`; your route handler never runs.
- `action === "CHALLENGE"` → middleware calls `next()`; your handler inspects `req.sentinel` and decides.
- `action === "ALLOW"` → middleware calls `next()`; request proceeds normally.

> **Always configure `trust proxy`.** Without it, Express reports `req.ip` as the loopback address and the IP-reputation signal never fires, capping scores well below BLOCK.

---

## 3. SDK reference

### 3.1 `SentinelClient`

Low-level wrapper around `POST /v1/evaluate`. Use directly when you want to evaluate outside a request handler (e.g. from a queue worker or a cron job).

```ts
import { SentinelClient } from "@sentinel/sdk";

const client = new SentinelClient({
  apiKey: process.env.SENTINEL_API_KEY!,
  endpoint: "http://localhost:8000",
  timeoutMs: 1500,
  failOpen: true,
});

const result = await client.evaluate({
  ip: "203.0.113.42",
  user_agent: "MyWorker/1.0",
  path: "/jobs/ingest",
  method: "POST",
  headers: { "x-request-id": "abc123" },
});

console.log(result.action, result.score);
```

**Constructor** — `new SentinelClient(opts: SentinelClientOptions)`

| Option | Type | Default | Notes |
| --- | --- | --- | --- |
| `apiKey` | `string` | **required** | Operator API key, issued by `POST /v1/operators`. |
| `endpoint` | `string` | `http://localhost:8000` | Base URL of the Sentinel backend. Trailing slash is stripped. |
| `timeoutMs` | `number` | `1500` | Per-call timeout. On expiry the request is aborted. |
| `failOpen` | `boolean` | `true` | If true, non-2xx responses and network errors return an ALLOW result. If false, they throw. |

**Methods**

- `evaluate(req: EvaluationRequest): Promise<EvaluationResult>` — see [types](#34-types).

### 3.2 `sentinel()` factory

Convenience factory that wraps `SentinelClient` + the Express middleware in a single call. Matches the README one-liner.

```ts
const s = sentinel({ apiKey });

app.use(s.middleware());          // Express middleware
await s.client.evaluate({ ... }); // low-level access to the same client
```

### 3.3 Framework adapters

All three adapters share identical semantics: evaluate on every request, attach the result to the request object, and short-circuit with `429` on BLOCK.

#### Express

```ts
import { expressMiddleware, SentinelClient } from "@sentinel/sdk";

const client = new SentinelClient({ apiKey });
app.use(expressMiddleware(client, {
  onDecision: (r) => metrics.counter("sentinel.decision", { action: r.action }).inc(),
}));
```

`req.sentinel` is typed via module augmentation — no `any` required.

#### Fastify

```ts
import Fastify from "fastify";
import { fastifyPlugin } from "@sentinel/sdk";

const app = Fastify();
await app.register(fastifyPlugin({ apiKey }));
```

Result is attached as `req.sentinel`.

#### Hono

```ts
import { Hono } from "hono";
import { honoMiddleware } from "@sentinel/sdk";

const app = new Hono();
app.use("*", honoMiddleware({ apiKey }));

app.get("/protected", (c) => {
  const decision = c.get("sentinel");
  return c.json({ action: decision?.action });
});
```

Result is stored under the `"sentinel"` context key.

### 3.4 Types

```ts
type Action = "ALLOW" | "CHALLENGE" | "BLOCK";

interface EvaluationRequest {
  ip: string;
  user_agent?: string;
  path?: string;
  method?: string;
  headers?: Record<string, string>;
  timestamp?: string; // ISO-8601. Server time is used if omitted.
}

interface EvaluationResult {
  action: Action;
  score: number;                          // 0–100, higher = more suspicious
  signals: Record<string, number>;        // per-signal contributions (0–1)
  fingerprint: string;                    // stable identifier for this actor
  eval_id: string;                        // correlation id, log this
}

interface SentinelClientOptions {
  apiKey: string;
  endpoint?: string;
  timeoutMs?: number;
  failOpen?: boolean;
}

interface MiddlewareOptions {
  costWeight?: number;                    // reserved for per-route cost weighting
  onDecision?: (r: EvaluationResult) => void;
}
```

### 3.5 Fail-open semantics

When `failOpen` is `true` (default), the client returns a synthetic ALLOW on any failure:

```ts
{
  action: "ALLOW",
  score: 0,
  signals: { fail_open: 1 },
  fingerprint: "0xfailopen",
  eval_id: "ev_failopen_<timestamp>",
}
```

The `fail_open: 1` signal in the result is the canonical way to detect this state. Log it, alarm on it, but do not let a Sentinel outage take down your signup endpoint. Set `failOpen: false` only when evaluation is strictly required (e.g. faucet payout).

---

## 4. HTTP API reference

### 4.1 `POST /v1/evaluate`

Evaluate a single request. Debits the operator's pool by `eval_cost_usdc` (default `$0.0001`) before running signals.

**Headers**

```
Authorization: Bearer <operator_api_key>
Content-Type: application/json
```

**Request body**

```json
{
  "ip": "203.0.113.42",
  "user_agent": "Mozilla/5.0 ...",
  "path": "/signup",
  "method": "POST",
  "headers": {
    "x-forwarded-for": "203.0.113.42",
    "accept-language": "en-US"
  },
  "timestamp": "2026-04-19T12:34:56Z"
}
```

Only `ip` is required. Supplying headers improves signal quality — `user-agent`, `accept-language`, and `x-forwarded-for` are used by the fingerprint extractor.

**200 OK**

```json
{
  "action": "CHALLENGE",
  "score": 58,
  "signals": {
    "ip_asn": 0.7,
    "cadence": 0.4,
    "endpoint_diversity": 0.0,
    "error_rate": 0.0,
    "reputation": 0.62
  },
  "fingerprint": "fp_7c9d3e…",
  "eval_id": "ev_4a1b…"
}
```

**Decision thresholds**

| Score | Action |
| --- | --- |
| `< 40` | `ALLOW` |
| `40–64` | `CHALLENGE` |
| `≥ 65` | `BLOCK` |

See [Decision semantics](#5-decision-semantics) for the underlying signal weights.

**402 Payment Required** — operator pool empty:

```json
{
  "detail": {
    "error": "operator_pool_empty",
    "balance": 0.0,
    "refill_url": "/v1/operators/op_abc123/credit"
  }
}
```

**401 Unauthorized** — missing or unknown API key.

### 4.2 Operator management

Operators own an API key and a USDC pool. In dummy mode, `POST /v1/operators` auto-seeds `$100` so you can integrate without wiring payments.

#### `POST /v1/operators`

```json
{ "name": "Acme Signup API" }
```

Response (`201`):

```json
{
  "operator": {
    "id": "op_abc123",
    "name": "Acme Signup API",
    "api_key": "sk_live_…"
  },
  "pool": {
    "operator_id": "op_abc123",
    "balance_usdc": 100.0
  }
}
```

Store the `api_key` — it is only returned once.

#### `GET /v1/operators/{operator_id}`

Returns the current pool balance.

```json
{ "operator_id": "op_abc123", "balance_usdc": 42.137 }
```

Returns `404` if the operator does not exist.

#### `POST /v1/operators/{operator_id}/credit`

Credits the pool. In full mode this is invoked by the onchain `OperatorPool` deposit hook; in dummy mode it takes an arbitrary amount for testing.

```json
{ "amount_usdc": 50.0 }
```

Response:

```json
{ "operator_id": "op_abc123", "balance_usdc": 92.137 }
```

### 4.3 Dashboard

Read-only endpoints powering the Vue dashboard. Rate-limit in front of them in production.

| Endpoint | Query params | Returns |
| --- | --- | --- |
| `GET /v1/dashboard/events` | `limit` (1–500, default 100), `since` (cursor from prev response) | Ring buffer of recent evaluations, newest first, plus counts by action and a cursor for long-polling. |
| `GET /v1/dashboard/timeseries` | `window` seconds (30–3600, default 300), `bucket` seconds (1–300, default 5) | Bucket-aligned series `allow` / `challenge` / `block` / `avg_score` plus `timestamps` and `partial_fraction` (0–1, how far into the rightmost in-progress bucket). |
| `GET /v1/dashboard/fingerprints` | `limit` (1–50, default 10) | Top flagged fingerprints ranked by `max_score` then `hits`. Includes the operators that observed them. |
| `GET /v1/dashboard/operators` | — | All operators with live pool balances and `eval_cost_usdc` (so a client can compute evals-remaining). |

> **Timeseries bucket edges are clock-aligned.** Edges are snapped to absolute-time multiples of `bucket` seconds. Polling faster than one bucket is wasted work — the chart will render the same grid.

### 4.4 Health

#### `GET /health`

```json
{ "status": "ok", "dummy_mode": true }
```

Used by the dashboard status dot and by uptime probes. Always returns `200` when the process is up; `status` reflects internal subsystem liveness.

---

## 5. Decision semantics

Signals produce a value in `[0, 1]` where `1` means "strong evidence of abuse." The final score is a weighted average scaled to `0–100`:

```
score = 100 * Σ(value_i * weight_i) / Σ(weight_i)
```

| Signal | Weight | What it measures |
| --- | --- | --- |
| `ip_asn` | 0.6 | Residential-proxy / datacenter / known-bad ASN prefixes. |
| `cadence` | 1.2 | Sliding-window burst rate from the same fingerprint. |
| `endpoint_diversity` | 0.5 | Same fingerprint hitting an implausibly broad set of routes. |
| `error_rate` | 0.7 | Recent 4xx/5xx ratio attributable to this fingerprint. |
| `reputation` | 1.5 | Cross-operator reputation (EMA of past scores, shared across all apps). |

Cross-operator reputation is the reason Sentinel improves with scale: each evaluation updates the ledger, and future evaluations — on any integrated API — start from that prior.

---

## 6. Error model

All non-2xx responses follow FastAPI's shape:

```json
{ "detail": "human-readable reason" }
```

or for structured errors:

```json
{ "detail": { "error": "code", ...context } }
```

| Status | Meaning |
| --- | --- |
| `400` | Malformed request body. |
| `401` | Missing or invalid API key. |
| `402` | Operator pool is empty. Credit the pool and retry. |
| `404` | Unknown operator. |
| `422` | Pydantic validation error — check field types. |
| `429` | (SDK-originated, not backend) The middleware returns this when the backend's decision is `BLOCK`. |
| `5xx` | Backend failure. SDK defaults to fail-open. |

---

## 7. Operational notes

- **Clock skew.** `timestamp` is optional. If you supply it, drift > 60 s is ignored and server time is substituted. Signals that rely on wall-clock recency (cadence) use server time.
- **Fingerprint stability.** The fingerprint is derived from IP + ASN + user-agent + selected headers. It intentionally *does not* include a login cookie or bearer token, so it survives logout and catches shared credentials.
- **Idempotency.** `POST /v1/evaluate` is safe to retry. Each call debits the pool and writes a new reputation sample; retries inflate volume but produce consistent decisions.
- **Concurrency.** The backend is single-process async; run behind `uvicorn --workers N` in production. Redis-backed cadence counters are required to scale past one worker (see [PLAN.md](./PLAN.md)).
- **Dummy mode.** Set `SENTINEL_DUMMY=true` or pass `-- --dummy`. Payments, reputation cache, and store are in-memory; data is lost on restart. Use for local integration only.
- **Observability.** Every decision is logged as a structured `evaluate` event with `eval_id`, `operator`, `fingerprint`, `score`, `action`. Correlate with your request logs via `eval_id`.
