<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import Label from '../components/Label.vue';
import Divider from '../components/Divider.vue';
import Footer from '../components/Footer.vue';
import CodeBlock from '../components/CodeBlock.vue';
import HeroHeading from '../components/HeroHeading.vue';
import HeroSvg from '../components/HeroSvg.vue';
import { useReveal } from '../composables/useReveal.js';

const router = useRouter();
const root = ref(null);
useReveal(root);

const services = [
  {
    n: '01', label: 'Core API', title: 'The evaluate endpoint',
    desc: 'One POST call. Every signal resolved.',
    detail: 'POST /v1/evaluate accepts a fingerprint (derived from IP + ASN + user-agent + selected headers) and returns a score (0–100) and a signal (ALLOW / CHALLENGE / BLOCK) in milliseconds. The response also includes a breakdown of each contributing signal weight so you can log, debug, and tune your routing logic.',
    specs: ['< 40ms p99 latency', 'Score 0–100 + discrete signal', 'Full signal breakdown in response', 'Idempotent — safe to call multiple times per request'],
    code: `// POST /v1/evaluate
fetch('https://api.sentinelprotocol.io/v1/evaluate', {
  method: 'POST',
  headers: { 'Authorization': 'Bearer sk_live_...', 'Content-Type': 'application/json' },
  body: JSON.stringify({
    ip: req.ip,
    userAgent: req.headers['user-agent'],
    asn: req.headers['x-asn'],
    endpoint: req.path,
  }),
}).then(r => r.json())
// → { score: 78, signal: "BLOCK", fingerprint: "a3f7...", breakdown: {...} }`,
  },
  {
    n: '02', label: 'Scoring engine', title: 'Behavioral signals',
    desc: 'Six inputs. One score.',
    detail: 'Request cadence (burst rate over a sliding window), endpoint diversity (breadth of routes hit), error rate (4xx and 5xx proportion), IP reputation (fed by internal and third-party blocklists), cross-operator history (the EMA from the Arc L1 ledger), and ASN reputation. Each signal carries a configurable weight; cross-operator history is the strongest at 1.5×.',
    specs: ['6 behavioral signals, all weighted', 'Cross-operator EMA at weight 1.5×', 'Configurable thresholds per operator', 'Explainable — every score has a reason'],
  },
  {
    n: '03', label: 'Reputation ledger', title: 'Arc L1 onchain storage',
    desc: 'Portable reputation across every operator.',
    detail: 'The ReputationLedger contract on Arc L1 stores fingerprint hashes and their EMA scores — never raw payloads, never PII. Writes are batched (not per-request) to minimize chain overhead. When a new operator evaluates a fingerprint, the onchain prior is read as the heaviest signal. Flagged on one API means flagged on all of them — automatically, without coordination.',
    specs: ['EMA formula: 70% prior + 30% new', 'Batched writes — not per-request', 'Only hashes and numeric scores onchain', 'No PII, no payload, no user identity'],
  },
  {
    n: '04', label: 'Billing', title: 'Circle Nanopayments (x402)',
    desc: 'Pay-per-call. Settled in USDC.',
    detail: 'Sentinel uses Circle Nanopayments over the x402 / Gateway protocol on Arc L1. Top up your operator pool with a credit card, ACH, or USDC directly. Each evaluation debits a fraction of a cent. No monthly seat fee, no minimum spend. A solo project can scale to zero; a spike-season product scales linearly without renegotiating a contract.',
    specs: ['Fractions of a cent per evaluation', 'USDC settlement on Arc L1', 'Top up via card, ACH, or crypto', 'No seats, no contracts, no minimums'],
  },
  {
    n: '05', label: 'SDK', title: 'Express / Fastify / Hono middleware',
    desc: "app.use(sentinel({ apiKey })) and you're done.",
    detail: 'The SDK is a thin wrapper over one HTTP call. It attaches req.sentinel to every request with score, signal, and fingerprint. Returns 429 on BLOCK before your handler runs. Passes through cleanly on ALLOW. Exposes req.sentinel.signal === "CHALLENGE" for your custom routing. No lock-in — if you outgrow the SDK, drop down to the raw HTTP API.',
    specs: ['Express / Fastify / Hono support', 'req.sentinel.score, .signal, .fingerprint', 'Auto-429 on BLOCK', 'No lock-in — HTTP API always available'],
    code: `npm install @sentinel/sdk

import { sentinel } from '@sentinel/sdk';

// One line — covers ALLOW, CHALLENGE, BLOCK
app.use(sentinel({ apiKey: process.env.SENTINEL_KEY }));

// Access the signal anywhere downstream
app.post('/login', (req, res) => {
  const { score, signal } = req.sentinel;
  if (signal === 'BLOCK')     return res.sendStatus(429);
  if (signal === 'CHALLENGE') return res.json({ mfa: true });
  // proceed...
});`,
  },
  {
    n: '06', label: 'Storage tiers', title: 'Three-tier state architecture',
    desc: 'Hot, warm, and durable — in one evaluation.',
    detail: 'Redis holds burst state (last N seconds of request cadence per fingerprint). Postgres holds recent samples for trend analysis. The Arc L1 ledger holds the durable, cross-operator EMA. Each evaluation reads all three tiers in parallel; the combined signal is what determines your score. No tier is skipped, even on a cold fingerprint.',
    specs: ['Redis: hot/burst state', 'Postgres: recent sample window', 'Arc L1: durable cross-operator EMA', 'All three tiers read in parallel per call'],
  },
];
</script>

<template>
  <div ref="root">
    <section class="hero container">
      <div class="hero-grid">
        <div class="hero-left">
          <Label>Services</Label>
          <HeroHeading line1="One endpoint." line2="Every signal." />
          <p class="reveal lead">
            Sentinel's trust evaluation stack — from the HTTP endpoint to the onchain reputation ledger. Each component is independently documented and queryable.
          </p>
        </div>
        <HeroSvg variant="services" />
      </div>
      <Divider />
    </section>

    <template v-for="(svc, i) in services" :key="svc.n">
      <section class="container svc">
        <div class="svc-grid">
          <div class="sticky reveal">
            <Label>{{ svc.label }}</Label>
            <div class="svc-title">{{ svc.title }}</div>
            <p class="svc-desc">{{ svc.desc }}</p>
          </div>
          <div class="svc-body">
            <p class="reveal detail">{{ svc.detail }}</p>
            <div class="specs reveal">
              <div
                v-for="(spec, j) in svc.specs"
                :key="j"
                class="spec"
                :class="{ alt: j % 2 === 0, bottom: j < 2, right: j % 2 === 0 }"
              >
                <div class="dot" />
                <span>{{ spec }}</span>
              </div>
            </div>
            <CodeBlock v-if="svc.code">{{ svc.code }}</CodeBlock>
          </div>
        </div>
      </section>
      <Divider />
    </template>

    <section class="end-cta">
      <h2 class="end-h2 reveal">Ready to integrate?</h2>
      <p class="end-p reveal">API key in minutes. No credit card required to start.</p>
      <button class="btn btn-primary btn-press reveal" @click="router.push('/contact')">Request access</button>
    </section>

    <Footer />
  </div>
</template>

<style scoped>
.hero { padding-top: 80px; padding-bottom: 80px; }
.hero-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 64px; align-items: center; margin-bottom: 80px; }
.hero-grid > * { min-width: 0; }
.hero-left { display: flex; flex-direction: column; }
.hero-left .lead { margin-top: 24px; max-width: 400px; }
.lead { font-size: 17px; line-height: 1.65; color: var(--color-fg-secondary); letter-spacing: 0.1px; }

/* .svc inherits container's horizontal padding; vertical handled by .svc-grid */
.svc-grid { display: grid; grid-template-columns: 240px 1fr; gap: 64px; padding: 64px 0; align-items: start; }
.sticky { position: sticky; top: 80px; }
.svc-title { font-family: var(--font-display); font-size: 26px; font-weight: 400; line-height: 1.15; color: #000; margin: 12px 0; letter-spacing: -0.3px; }
.svc-desc { font-size: 14px; line-height: 1.55; color: var(--color-fg-muted); letter-spacing: 0.1px; }
.svc-body { display: flex; flex-direction: column; gap: 24px; min-width: 0; }
.svc-grid > * { min-width: 0; }
.detail { font-size: 16px; line-height: 1.7; color: var(--color-fg-secondary); letter-spacing: 0.1px; }

.specs {
  display: grid; grid-template-columns: 1fr 1fr; gap: 0;
  border-radius: 12px; overflow: hidden; border: var(--border);
}
.spec {
  padding: 14px 18px; background: #fff; display: flex; gap: 10px; align-items: flex-start;
  transition: background 200ms ease;
}
.spec.alt { background: #fafafa; }
.spec.bottom { border-bottom: var(--border); }
.spec.right { border-right: var(--border); }
.spec:hover { background: #f0ede8; }
.spec .dot { width: 4px; height: 4px; background: var(--color-fg-muted); border-radius: 50%; margin-top: 7px; flex-shrink: 0; }
.spec span { font-size: 13px; line-height: 1.5; color: var(--color-fg-secondary); letter-spacing: 0.1px; }

.btn { display: inline-flex; align-items: center; justify-content: center; border: none; font-weight: 600; letter-spacing: 0.1px; }
.btn-primary { background: #000; color: #fff; padding: 12px 28px; border-radius: 9999px; font-size: 14px; }
.btn-primary:hover { opacity: 0.85; }

.end-cta { padding: 80px 28px; text-align: center; }
.end-h2 { font-family: var(--font-display); font-size: 40px; font-weight: 400; line-height: 1.1; color: #000; margin: 0 0 20px; letter-spacing: -0.8px; }
.end-p { font-size: 16px; color: var(--color-fg-secondary); line-height: 1.65; max-width: 400px; margin: 0 auto 32px; letter-spacing: 0.1px; }

@media (max-width: 900px) {
  .hero { padding-top: 40px; padding-bottom: 32px; }
  .hero-grid {
    grid-template-columns: 1fr;
    gap: 24px;
    align-items: start;
    margin-bottom: 32px;
  }
  .lead { font-size: 16px; }

  .svc-grid {
    grid-template-columns: 1fr;
    gap: 20px;
    padding: 48px 0;
  }
  .sticky { position: static; top: auto; }
  .svc-title { font-size: 22px; margin: 8px 0; }
  .svc-desc { font-size: 13px; }
  .svc-body { gap: 20px; }
  .detail { font-size: 15px; line-height: 1.65; }

  .specs { grid-template-columns: 1fr; }
  .spec { padding: 12px 16px; }
  .spec.bottom { border-bottom: var(--border); }
  .spec.right { border-right: none; }
  .spec:last-child { border-bottom: none !important; }

  .end-cta { padding: 56px 20px; }
  .end-h2 { font-size: clamp(26px, 7vw, 36px); }
}
@media (max-width: 420px) {
  .svc-grid { padding: 36px 0; }
  .spec { padding: 11px 14px; }
  .spec span { font-size: 13px; }
}
</style>
