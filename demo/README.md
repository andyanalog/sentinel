# Sentinel Demo

Two demo operators (App A + App B) behind the Sentinel SDK, plus a bot simulator that shows cross-app reputation kick-in.

## Run (dummy mode — zero deps)

```bash
# 1. start backend in dummy mode
cd ../backend && SENTINEL_DUMMY=true uvicorn sentinel.main:app --reload

# 2. install demo deps (pulls @sentinel/sdk via file:../sdk)
cd ../demo && npm install

# 3. start App A
PORT=3000 APP_NAME="App A" SENTINEL_API_KEY=demo-app-a npx tsx index.ts

# 4. in another shell, start App B
PORT=3001 APP_NAME="App B" SENTINEL_API_KEY=demo-app-b npx tsx index.ts

# 5. run the bot against App A first (builds reputation)
npx tsx bot.ts --target=http://localhost:3000 --rps=20 --duration=10

# 6. run the bot against App B — should block immediately via shared ledger
npx tsx bot.ts --target=http://localhost:3001 --rps=5 --duration=5
```

## What to watch

- App A's backend logs: score degrading, BLOCK firing after ~20 req
- Dummy ledger logs: `dummy_ledger.write_batch` with fake tx hash
- Dummy payments logs: `dummy_payments.debit` with dropping balance
- App B call: **first request blocked**, because the fingerprint is already in the shared ledger
