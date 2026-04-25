import express from "express";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { sentinel } from "@sentinel/sdk";
// Pull in the Express Request.sentinel type augmentation.
import "@sentinel/sdk/express";
import type { EvaluationResult } from "@sentinel/sdk";

// Local helper: the SDK augments Express.Request.sentinel, but the project's
// tsconfig (`"types": ["node"]`) narrows ambient types and swallows the
// augmentation. Read through this helper instead of `req.sentinel` directly.
const evalOf = (req: express.Request): EvaluationResult | undefined =>
  (req as unknown as { sentinel?: EvaluationResult }).sentinel;

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const PORT = Number(process.env.PORT ?? 3000);
const SENTINEL_ENDPOINT = process.env.SENTINEL_ENDPOINT ?? "http://localhost:8000";
const API_KEY = process.env.SENTINEL_API_KEY ?? "demo-app-a";
const APP_NAME = process.env.APP_NAME ?? "Sentinel Demo";
const LEDGER_EXPLORER_URL = process.env.LEDGER_EXPLORER_URL ?? "";

// SSE broadcast hub — every decision is fanned out to connected browsers.
type DecisionEvent = {
  t: number;
  ip: string;
  score: number;
  action: EvaluationResult["action"];
  fingerprint: string;
  source: "user" | "bot";
};
const sseClients = new Set<express.Response>();
const broadcast = (ev: DecisionEvent) => {
  const line = `data: ${JSON.stringify(ev)}\n\n`;
  for (const res of sseClients) res.write(line);
};

const trust = sentinel({
  apiKey: API_KEY,
  endpoint: SENTINEL_ENDPOINT,
  failOpen: true,
});

const app = express();
// Trust X-Forwarded-For so req.ip reflects the real client (the bot simulator
// spoofs XFF). Without this, req.ip is always 127.0.0.1 and the IP-based
// signal can't distinguish traffic from a Tor exit vs a browser.
app.set("trust proxy", true);
app.use(express.json());
app.use(express.static(path.join(__dirname, "public")));

const scoredRaw = trust.middleware();
// SDK middleware is async — await it so we always run our broadcast,
// including on BLOCK (where the SDK short-circuits with a 429 and never
// invokes next()). req.sentinel is set by the SDK before that short-circuit.
const scoredWithTag: express.RequestHandler = async (req, res, next) => {
  let nextErr: unknown = undefined;
  let nextWasCalled = false;
  await (scoredRaw as unknown as (
    r: express.Request, s: express.Response, n: (e?: unknown) => void,
  ) => Promise<void>)(req, res, (err?: unknown) => {
    nextWasCalled = true;
    nextErr = err;
  });
  const s = evalOf(req);
  if (s) {
    const source: DecisionEvent["source"] =
      (req.headers["x-sentinel-source"] as string) === "bot" ? "bot" : "user";
    broadcast({
      t: Date.now(),
      ip: (req.ip ?? "?") as string,
      score: s.score,
      action: s.action,
      fingerprint: s.fingerprint,
      source,
    });
  }
  if (nextWasCalled) next(nextErr as Error | undefined);
};

// ── API ──
app.get("/api/config", (_req, res) => {
  res.json({
    app: APP_NAME,
    endpoint: SENTINEL_ENDPOINT,
    explorer: LEDGER_EXPLORER_URL,
  });
});

app.get("/api/events", (req, res) => {
  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.flushHeaders?.();
  res.write(": connected\n\n");
  sseClients.add(res);
  req.on("close", () => sseClients.delete(res));
});

// Protected endpoints — same pattern the SDK README shows.
app.post("/api/submit", scoredWithTag, (req, res) => {
  const s = evalOf(req);
  res.json({
    ok: true,
    score: s?.score ?? null,
    action: s?.action ?? null,
    eval_id: s?.eval_id ?? null,
  });
});

app.get("/api/ping", scoredWithTag, (req, res) => {
  const s = evalOf(req);
  res.json({
    ok: true,
    score: s?.score ?? null,
    action: s?.action ?? null,
  });
});

// Internal bot-loop so judges don't need a shell to fire the attack.
app.post("/api/attack", async (req, res) => {
  const rps = Math.min(60, Math.max(1, Number(req.body?.rps ?? 30)));
  const durationSec = Math.min(20, Math.max(1, Number(req.body?.duration ?? 10)));
  const botIp = (req.body?.ip as string) ?? randomBotIp();
  const self = `http://127.0.0.1:${PORT}`;
  const total = rps * durationSec;
  const intervalMs = 1000 / rps;
  let fired = 0;
  res.json({ ok: true, total, rps, durationSec, ip: botIp });

  const timer = setInterval(() => {
    if (fired >= total) {
      clearInterval(timer);
      return;
    }
    fired++;
    fetch(`${self}/api/submit`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-forwarded-for": botIp,
        "user-agent": "BurstBot/1.0",
        "x-sentinel-source": "bot",
      },
      body: JSON.stringify({ data: "spam" }),
    }).catch(() => {
      /* ignore */
    });
  }, intervalMs);
});

function randomBotIp(): string {
  // Pool of plausibly-sketchy prefixes so the demo reads as realistic
  // without pointing at real addresses.
  const pool = ["185.220.1", "45.134.26", "194.127.172", "212.83.146"];
  const prefix = pool[Math.floor(Math.random() * pool.length)];
  return `${prefix}.${Math.floor(Math.random() * 254) + 1}`;
}

app.listen(PORT, () => {
  console.log(`[${APP_NAME}] listening on :${PORT} → sentinel ${SENTINEL_ENDPOINT}`);
});
