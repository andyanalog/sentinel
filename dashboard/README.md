# Sentinel Dashboard

Real-time operator console. Polls the backend and surfaces:

- KPIs: total / allowed / challenged / blocked (with block rate)
- Live stream of the last 100 evaluations (action, score, fingerprint, top signals, operator)
- Top flagged fingerprints across all operators — the cross-app reputation view
- Operator pool balances, eval cost, evaluations remaining

Built with Vue 3 + PrimeVue (Aura theme). Vercel-style: white background, Inter typography, monospace hashes.

## Run

```bash
# in one shell — backend
cd ../backend && SENTINEL_DUMMY=true uvicorn sentinel.main:app --reload

# in another shell — dashboard
cd dashboard
npm install
npm run dev
# → http://localhost:5173
```

Point at a non-default backend:

```bash
VITE_SENTINEL_API=http://localhost:8000 npm run dev
```

## Driving traffic

With the demo app running, use the bot simulator or hit `/v1/evaluate` directly. Events flow into the KPIs within ~1 second and populate the live table.
