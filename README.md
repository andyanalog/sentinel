# Sentinel — Trust-as-a-Service

Middleware trust evaluation service. Any API calls `/v1/evaluate` per request for an ALLOW / CHALLENGE / BLOCK signal. Operators pay per evaluation via Circle Nanopayments (x402 / Gateway) on Arc L1. Reputation accumulates onchain across every integrated app.

See [PLAN.md](./PLAN.md) for full architecture and [REFERENCE.md](./REFERENCE.md) for the SDK and HTTP API reference.

## What it is (and what it isn't)

**What it does.** On every request that hits your API, Sentinel derives a *fingerprint* (a hash of IP + ASN + user-agent + selected headers) and a *score* (0–100) from behavioral signals — request cadence, endpoint diversity, error rate, IP reputation, and cross-operator history. That score maps to `ALLOW` / `CHALLENGE` / `BLOCK`. The fingerprint's running reputation is stored across three tiers: Redis for hot/burst state, Postgres for recent samples, and the Arc L1 `ReputationLedger` contract for the durable, cross-operator EMA (70% prior + 30% new, batched — not written per request). When a different operator later evaluates the same fingerprint, the onchain prior is read back as the heaviest signal (`reputation`, weight 1.5). That's the mechanism behind "flagged on one API = flagged everywhere."

**What it is not.** It does **not** store the request payload, headers, or any PII onchain — only fingerprint hashes and numeric scores. It is **not** a user-identity or KYC system; it never sees the logged-in user and intentionally excludes cookies/bearer tokens from the fingerprint so it survives logout and catches shared credentials. It is **not** a WAF or DDoS edge — put it behind Cloudflare, not in front of it. It is **not** a CAPTCHA replacement on its own; `CHALLENGE` is a hint that *your* app should route to a captcha, email verification, or slow path. It is **not** a deterministic rule engine — two identical requests can score differently as the cross-operator reputation evolves, which is the point.

## Core value props

- **Pay-per-call.** No monthly seat fee, no minimum. Scales to zero for a side project; scales linearly under a credential-stuffing spike. Settled in USDC via Circle Nanopayments (x402) so a $9/mo floor never blocks integration.
- **Blockchain abstracted away from the developer.** You never touch a wallet, a chain ID, or a gas estimator. Top up the operator pool with a card, ACH, or USDC — or pre-pay a monthly budget and let the per-call debit draw it down. The onchain ledger is an implementation detail; the integration surface is one HTTP call and one API key. Crypto is how we settle and how reputation becomes portable; it is not a requirement to use the product.
- **Cross-app reputation (built for developers).** The primary audience is builders — anyone shipping an API, signup flow, or LLM endpoint. You inherit the collective knowledge of every other integrator: bad IPs, abusive fingerprints, and scraper patterns that have already burned reputation elsewhere. A solo founder on day one gets the same signal quality as a funded company that's been integrated for a year.
- **Cross-app reputation (the mechanism).** A fingerprint flagged on one integrated API is flagged on all of them. The bad actor hitting your signup endpoint this morning already burned their reputation on someone else's login endpoint last night — you inherit that signal for free.
- **One-liner SDK.** `app.use(sentinel({ apiKey }))` for Express / Fastify / Hono. Returns 429 on BLOCK, attaches `req.sentinel` for CHALLENGE routing. No SDK lock-in — it's a thin wrapper over one HTTP call.

### A note on rotating IPs

Consumer residential IPs rotate every 24–48 hours, and this does produce a new fingerprint. It's a real limitation, handled with layered defenses rather than a silver bullet:

- **ASN reputation survives the rotation.** When the IP flips from `203.0.113.42` to `203.0.113.189` on the same ISP, the ASN stays the same — and the `ip_asn` signal and a coarser ASN-level reputation prior still fire.
- **Behavioral signals catch the new fingerprint fast.** Cadence and endpoint-diversity signals don't need history; the first burst from a new fingerprint is enough to trigger CHALLENGE within seconds.
- **Non-IP components are sticky.** User-agent, accept-language, and header ordering tend to persist across IP rotations from the same device, so the fingerprint isn't purely IP-derived.
- **The system is probabilistic, not a bouncer.** The goal is to raise the cost of abuse, not to make a perfect decision on request 1. A rotating-IP attacker pays in friction every 24h; a legitimate user on a rotating IP lands back in ALLOW after one or two low-risk requests.

For sophisticated attackers using residential-proxy networks that rotate per-request, the roadmap adds TLS JA4 fingerprinting and (browser-client only) canvas/WebGL signals. Those close the gap but can't be applied to pure API traffic.

## Real-world scenarios

**Signup / registration endpoints fighting fake account farms.**
The classic fraud surface. Incumbent answer is Cloudflare Turnstile or hCaptcha — widgets that fire once at form submit and can't see behavior across your other routes. Sentinel evaluates every request, carries reputation across endpoints (signup → first login → first write), and costs cents per thousand instead of a Turnstile Enterprise contract. Better fit when your abuse signal shows up *after* signup (e.g. burst API calls from a newly-created account).

**LLM / AI inference APIs under scraper and token-farming pressure.**
OpenAI-wrapper products get hammered by actors cycling free-tier keys to resell inference. Rate-limiting by API key is trivially bypassed; rate-limiting by IP punishes legitimate shared-NAT users. Sentinel fingerprints across key+IP+ASN+cadence and shares the reputation with every other LLM wrapper on the network — a scraper burning through free tiers on competitor A is pre-flagged when it hits you. Cloudflare Bot Management can do per-site rate limits but not cross-tenant reputation.

**Login endpoints defending against credential stuffing.**
Auth0/Okta anomaly detection and Stytch device intelligence work, but they're priced for enterprise SSO ($0.02–$0.25 per MAU) and only see *your* tenant's traffic. Sentinel sees the same credential-stuffing botnet hitting a dozen other login endpoints simultaneously and blocks it on request 1, not request 100. Pay-per-eval pricing means a hobbyist auth flow can afford the same signal quality as a funded startup.

**Free-tier abuse on SaaS and developer APIs.**
Image generation, email sending, code execution sandboxes — anywhere "free tier" means "unit economics depend on abuse staying below X%." Castle.io and Arkose Labs solve this but require 6-figure ACVs and enterprise sales cycles. Sentinel gives you the same ALLOW/CHALLENGE/BLOCK decision for a fraction of a cent per call with an afternoon of integration.

**Review, comment, and UGC spam.**
Akismet works for WordPress-shaped content but is blind to the upstream request pattern (same fingerprint posting to ten unrelated sites in a minute). Sentinel's cross-app signal catches coordinated spam rings before the content-level classifier sees the payload, which is strictly cheaper than running an LLM moderation pass on garbage.

**Crypto faucets, airdrop claims, and quest platforms.**
Sybil resistance is the entire product requirement. Gitcoin Passport and Worldcoin solve identity but require the user to actively enroll; most faucet users won't. Sentinel runs silently in the request path, flags the same wallet-farming fingerprint across every faucet on the network, and settles its own fees in the same USDC the faucet is already handling. Natural fit: onchain product, onchain payment rail, onchain reputation ledger.

## Quickstart (dummy mode — no external deps)

```bash
# backend
cd backend
pip install -e .
uvicorn sentinel.main:app --reload --host 0.0.0.0 --port 8000 -- --dummy
# or: SENTINEL_DUMMY=true uvicorn sentinel.main:app --reload

# demo app
cd demo && npm install && npx tsx index.ts

# bot simulator
npx tsx demo/bot.ts --target=http://localhost:3000 --rps=20
```

## Full mode

```bash
docker-compose up -d          # postgres + redis
cd backend && alembic upgrade head
uvicorn sentinel.main:app --host 0.0.0.0 --port 8000
```

## Layout

- `backend/` — FastAPI evaluation engine
- `sdk/` — TypeScript SDK (Express / Fastify / Hono)
- `demo/` — demo Express app + bot simulator
- `contracts/` — Vyper contracts for Arc L1
