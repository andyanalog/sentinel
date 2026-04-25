<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

import Label from '../components/Label.vue';
import Divider from '../components/Divider.vue';
import Footer from '../components/Footer.vue';
import AccordionItem from '../components/AccordionItem.vue';
import CodeBlock from '../components/CodeBlock.vue';
import ScoreViz from '../components/ScoreViz.vue';
import Ticker from '../components/Ticker.vue';
import HeroHeading from '../components/HeroHeading.vue';
import HeroSvg from '../components/HeroSvg.vue';
import { useReveal } from '../composables/useReveal.js';

const router = useRouter();
const root = ref(null);
const heroCopy = ref(null);
const heroLabel = ref(null);

const features = [
  { n: '01', title: 'Fingerprint derivation', body: 'Every request yields a deterministic hash of IP + ASN + user-agent + selected headers. No PII, no cookies, no bearer tokens — just the immutable shape of a request.' },
  { n: '02', title: 'Behavioral scoring', body: 'A 0–100 score built from request cadence, endpoint diversity, error rate, IP reputation, and your cross-operator history. ALLOW / CHALLENGE / BLOCK — in one response field.', defaultOpen: true, img: true },
  { n: '03', title: 'Blockchain-abstracted reputation', body: 'The fingerprint\'s EMA (70% prior + 30% new) lives in the Arc L1 ReputationLedger. Flagged on one API, flagged everywhere — without you touching a wallet or chain ID.' },
  { n: '04', title: 'Pay-per-call billing', body: 'Settled in USDC via Circle Nanopayments. Top up with card, ACH, or crypto. No monthly seat fee, no minimum. Scales to zero for a side project; scales linearly under a spike.' },
  { n: '05', title: 'One-liner SDK integration', body: 'app.use(sentinel({ apiKey })) for Express, Fastify, or Hono. Returns 429 on BLOCK, attaches req.sentinel for CHALLENGE routing. Under 10 minutes to production.' },
];

const howItWorks = [
  { label: 'Receive',  title: 'Request arrives at your API',    body: 'Your middleware intercepts the inbound request before it touches your business logic.' },
  { label: 'Evaluate', title: 'Sentinel scores the fingerprint', body: 'One HTTP call to /v1/evaluate. Redis hot-state + Postgres samples + Arc L1 ledger — resolved in milliseconds.' },
  { label: 'Decide',   title: 'ALLOW, CHALLENGE, or BLOCK',     body: 'Route based on the signal. Pass through, step up to CAPTCHA, or return 429. Your logic, our signal.' },
];

const tools = [
  { title: 'Access behavioral signal data across every integrated API', body: 'The cross-operator reputation prior is the heaviest signal. A bad actor burning reputation on one endpoint is pre-flagged on yours.' },
  { title: 'Automate responses from verified chain events', body: 'CHALLENGE triggers route to your captcha, email verification, or slow path. BLOCK returns 429 before your handler runs.' },
  { title: 'Verify transaction settlement without custom RPC calls', body: 'Nanopayments settle in USDC. Top up once; Sentinel draws down per evaluation. No gas estimation, no wallet management.' },
];

const insights = [
  { tag: 'Case Study', title: 'LLM APIs under scraper pressure', desc: 'How cross-operator reputation pre-flags token farmers before they touch your free tier.', signal: 'BLOCK' },
  { tag: 'Deep Dive',  title: 'Credential stuffing at scale',     desc: 'Why Auth0 anomaly detection sees your tenant. Sentinel sees the botnet hitting all twelve.', signal: 'CHALLENGE' },
  { tag: 'Case Study', title: 'Sybil resistance for Web3 faucets', desc: 'Silent fingerprinting, zero user friction. Same USDC rail the faucet already settles in.', signal: 'ALLOW' },
];

const codeSnippet = `npm install @sentinel/sdk

// Express / Fastify / Hono
import { sentinel } from '@sentinel/sdk';

app.use(sentinel({ apiKey: process.env.SENTINEL_KEY }));

// That's it. On every request:
// req.sentinel.score       → 0–100
// req.sentinel.signal      → ALLOW | CHALLENGE | BLOCK
// req.sentinel.fingerprint → sha256 hash

// Custom routing:
app.post('/signup', (req, res) => {
  if (req.sentinel.signal === 'CHALLENGE') {
    return res.json({ challenge: true });
  }
  // ... your logic
});`;

useReveal(root);

onMounted(() => {
  // Hero right-column copy intro
  const tl = gsap.timeline({ delay: 0.1 });
  tl.from(heroLabel.value, { opacity: 0, y: 8, duration: 0.6, ease: 'power3.out' })
    .from(heroCopy.value, { opacity: 0, y: 14, duration: 0.7, ease: 'power3.out' }, '-=0.35');
});
</script>

<template>
  <div ref="root">
    <!-- HERO -->
    <section class="hero container">
      <div class="hero-grid">
        <div class="hero-left">
          <div ref="heroLabel"><Label>Trust-as-a-Service</Label></div>
          <HeroHeading line1="Every request," line2="scored." />
          <p ref="heroCopy" class="lead">
            Sentinel evaluates any API call in real time — returning ALLOW, CHALLENGE, or BLOCK from behavioral signals and cross-operator reputation stored on Arc L1.
          </p>
        </div>
        <HeroSvg variant="home" />
      </div>
    </section>

    <Ticker />

    <!-- HOW IT WORKS -->
    <section class="container section">
      <div class="two-col">
        <div class="reveal">
          <Label>How it works</Label>
          <p class="side-copy">One middleware call. Three possible outcomes.</p>
        </div>
        <div class="three-grid reveal">
          <div v-for="(step, i) in howItWorks" :key="i" class="step">
            <Label>{{ step.label }}</Label>
            <div class="step-title">{{ step.title }}</div>
            <p class="step-body">{{ step.body }}</p>
          </div>
        </div>
      </div>
    </section>

    <Divider />

    <!-- CORE MODULES -->
    <section class="container section">
      <div class="two-col">
        <div class="sticky">
          <div class="reveal"><Label>Core modules</Label></div>
          <h2 class="reveal h2">Infrastructure for trust evaluation</h2>
          <p class="reveal side-copy">
            Everything Sentinel derives from a single request — and how it persists across your entire network.
          </p>
        </div>
        <div>
          <div class="accordion">
            <AccordionItem
              v-for="f in features"
              :key="f.n"
              :n="f.n"
              :title="f.title"
              :body="f.body"
              :img="!!f.img"
              :default-open="!!f.defaultOpen"
            />
          </div>
        </div>
      </div>
    </section>

    <!-- SIGNAL SECTION -->
    <div class="grey-band">
      <section class="container section">
        <div class="two-col">
          <div>
            <div class="reveal"><Label>The signal</Label></div>
            <h2 class="reveal h2">What Sentinel sees per request</h2>
            <p class="reveal side-copy">
              Six behavioral signals combined into a single score. Read in milliseconds.
            </p>
          </div>
          <ScoreViz />
        </div>
      </section>
    </div>

    <!-- TOOLS -->
    <section class="container section">
      <div class="reveal" style="margin-bottom: 56px;">
        <Label>Tools for API-native systems</Label>
        <h2 class="big-h2">Built for developers,<br />not security teams.</h2>
      </div>
      <div class="tools">
        <div v-for="(t, i) in tools" :key="i" class="tool reveal" :class="{ bordered: i < tools.length - 1 }">
          <div class="square" />
          <div class="tool-title">{{ t.title }}</div>
          <p class="tool-body">{{ t.body }}</p>
        </div>
      </div>
    </section>

    <Divider />

    <!-- INTEGRATION -->
    <section class="container section">
      <div class="split">
        <div>
          <div class="reveal"><Label>One-liner integration</Label></div>
          <h2 class="reveal h2" style="margin-bottom: 24px;">Under 10 minutes to production.</h2>
          <p class="reveal body">
            A thin wrapper over one HTTP call. Express, Fastify, or Hono. No SDK lock-in — call /v1/evaluate directly if you prefer.
          </p>
          <button class="btn btn-primary btn-press" style="margin-top: 28px;" @click="router.push('/contact')">Request API key</button>
        </div>
        <CodeBlock>{{ codeSnippet }}</CodeBlock>
      </div>
    </section>

    <!-- INSIGHTS -->
    <div class="grey-band">
      <section class="container section">
        <div class="insights-head">
          <div class="reveal">
            <Label>Fresh insights &amp; deep dives</Label>
            <h2 class="h2" style="margin-top: 16px;">Real threats.<br />Real walkthroughs.</h2>
          </div>
          <button class="btn btn-ghost btn-press" @click="router.push('/cases')">All case studies →</button>
        </div>
        <div class="cards">
          <div
            v-for="(item, i) in insights"
            :key="i"
            class="card reveal"
            @click="router.push('/cases')"
          >
            <div class="card-top">
              <!-- BLOCK: concentric frames cut by a heavy bar -->
              <svg v-if="item.signal === 'BLOCK'" class="card-svg" viewBox="0 0 400 160" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
                <g fill="none" stroke="#ffffff" stroke-width="1">
                  <rect x="100" y="20" width="200" height="120" stroke-opacity="0.18" />
                  <rect x="120" y="32" width="160" height="96"  stroke-opacity="0.28" />
                  <rect x="140" y="44" width="120" height="72"  stroke-opacity="0.40" />
                  <rect x="160" y="56" width="80"  height="48"  stroke-opacity="0.55" />
                </g>
                <line x1="60" y1="80" x2="340" y2="80" stroke="#ffffff" stroke-opacity="0.85" stroke-width="2.5" />
                <circle cx="200" cy="80" r="5" fill="#ffffff" />
              </svg>

              <!-- CHALLENGE: a branching crossroads -->
              <svg v-else-if="item.signal === 'CHALLENGE'" class="card-svg" viewBox="0 0 400 160" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
                <g fill="none" stroke="#ffffff" stroke-width="1.2" stroke-linecap="round">
                  <path d="M40 80 L170 80" stroke-opacity="0.85" />
                  <path d="M170 80 L250 40 L360 40" stroke-opacity="0.55" />
                  <path d="M170 80 L250 80 L360 80" stroke-opacity="0.85" />
                  <path d="M170 80 L250 120 L360 120" stroke-opacity="0.55" />
                </g>
                <circle cx="170" cy="80" r="5" fill="#ffffff" />
                <circle cx="360" cy="40" r="3" fill="#ffffff" fill-opacity="0.8" />
                <circle cx="360" cy="80" r="3" fill="#ffffff" />
                <circle cx="360" cy="120" r="3" fill="#ffffff" fill-opacity="0.8" />
              </svg>

              <!-- ALLOW: parallel flow lines with a gate-through arrow -->
              <svg v-else class="card-svg" viewBox="0 0 400 160" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
                <g fill="none" stroke="#ffffff" stroke-width="1" stroke-linecap="round">
                  <path d="M0 34 L400 34"  stroke-opacity="0.22" />
                  <path d="M0 62 L400 62"  stroke-opacity="0.32" />
                  <path d="M0 98 L400 98"  stroke-opacity="0.32" />
                  <path d="M0 126 L400 126" stroke-opacity="0.22" />
                </g>
                <g fill="none" stroke="#ffffff" stroke-opacity="0.9" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M140 80 L260 80" />
                  <path d="M244 66 L260 80 L244 94" />
                </g>
              </svg>
            </div>
            <div class="card-body">
              <div class="tag">{{ item.tag }}</div>
              <div class="card-title">{{ item.title }}</div>
              <p class="card-desc">{{ item.desc }}</p>
            </div>
          </div>
        </div>
      </section>
    </div>

    <!-- CTA -->
    <section class="cta-wrap">
      <div class="cta-card reveal">
        <h2 class="cta-title">Inherit the network.<br />Block on request one.</h2>
        <p class="cta-body">
          Every operator on Sentinel hardens every other operator. Pay-per-call. No minimums. API key in minutes.
        </p>
        <div class="cta-btns">
          <button class="btn btn-primary btn-press" @click="router.push('/contact')">Get API access</button>
          <button class="btn btn-secondary btn-press" @click="router.push('/cases')">Read case studies</button>
        </div>
      </div>
    </section>

    <Footer />
  </div>
</template>

<style scoped>
.hero { padding-top: 80px; padding-bottom: 0; }
.hero-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 64px; align-items: center; }
.hero-left { display: flex; flex-direction: column; }
.hero-left .lead { margin-top: 28px; max-width: 420px; }
.hero-left .ctas { margin-top: 32px; }
.lead {
  font-size: 18px; line-height: 1.6; color: var(--color-fg-secondary);
  letter-spacing: 0.1px; max-width: 440px; margin: 0 0 32px;
}
.ctas { display: flex; gap: 10px; flex-wrap: wrap; }

.btn {
  display: inline-flex; align-items: center; justify-content: center;
  gap: 6px; border: none; font-size: 14px; font-weight: 500;
  letter-spacing: 0.1px;
  text-decoration: none; cursor: pointer;
}
a.btn-warm { color: #000; }
a.btn-warm:hover { color: #000; text-decoration: none; }
.btn-primary {
  background: #000; color: #fff; padding: 11px 22px; border-radius: 9999px;
  font-weight: 600;
}
.btn-primary:hover { opacity: 0.85; }
.btn-warm {
  background: #f5f2ef; color: #000; padding: 11px 22px; border-radius: 9999px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  box-shadow: var(--shadow-warm);
}
.btn-warm:hover { box-shadow: var(--shadow-warm-lift); }
.btn-secondary {
  background: #fff; color: #000; padding: 12px 24px; border-radius: 9999px;
  box-shadow: var(--shadow-card);
}
.btn-secondary:hover { box-shadow: var(--shadow-card-lift); }
.btn-ghost {
  background: none; color: #000; padding: 9px 18px; border-radius: 9999px;
  border: 1px solid rgba(0, 0, 0, 0.15); font-size: 13px;
}
.btn-ghost:hover { background: rgba(0, 0, 0, 0.04); }

.section { padding-top: 96px; padding-bottom: 96px; }
.section > *:first-child { }

.two-col { display: grid; grid-template-columns: 240px 1fr; gap: 64px; align-items: start; }
.sticky { position: sticky; top: 80px; }
.side-copy { font-size: 14px; line-height: 1.65; color: var(--color-fg-muted); margin-top: 12px; letter-spacing: 0.1px; }
.h2 {
  font-family: var(--font-display); font-size: 32px; font-weight: 400;
  line-height: 1.15; color: #000; margin: 16px 0; letter-spacing: -0.4px;
}

.three-grid {
  display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1px;
  background: rgba(0, 0, 0, 0.07); border-radius: 16px; overflow: hidden;
}
.step { background: #fff; padding: 32px 28px; display: flex; flex-direction: column; gap: 12px; transition: background 200ms ease; }
.step:hover { background: #fafafa; }
.step-title { font-family: var(--font-display); font-size: 22px; font-weight: 400; line-height: 1.2; color: #000; margin-top: 8px; }
.step-body { font-size: 14px; line-height: 1.65; color: var(--color-fg-secondary); letter-spacing: 0.1px; }

.accordion { border-top: var(--border); }

.grey-band { background: #f5f5f5; border-top: var(--border); border-bottom: var(--border); }

.big-h2 {
  font-family: var(--font-display); font-size: clamp(28px, 4vw, 52px);
  font-weight: 400; line-height: 1.1; color: #000;
  margin: 16px 0 0; letter-spacing: -1px; max-width: 680px;
}

.tools { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0; }
.tool { padding: 32px; display: flex; flex-direction: column; gap: 16px; }
.tool.bordered { border-right: var(--border); }
.square { width: 6px; height: 6px; background: #000; flex-shrink: 0; margin-top: 6px; }
.tool-title { font-family: var(--font-display); font-size: 20px; font-weight: 400; line-height: 1.25; color: #000; }
.tool-body { font-size: 14px; line-height: 1.65; color: var(--color-fg-secondary); letter-spacing: 0.1px; }

.split { display: grid; grid-template-columns: 1fr 1fr; gap: 80px; align-items: start; }
.body { font-size: 16px; line-height: 1.65; color: var(--color-fg-secondary); letter-spacing: 0.1px; }

.insights-head {
  display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 48px;
}
.cards { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }
.card {
  background: #fff; border-radius: 16px; overflow: hidden; box-shadow: var(--shadow-card);
  cursor: pointer; transition: transform 260ms cubic-bezier(0.22,1,0.36,1), box-shadow 260ms ease;
}
.card:hover { transform: translateY(-4px); box-shadow: var(--shadow-card-lift); }
.card-top {
  height: 160px;
  background: #0a0a0a;
  position: relative;
  overflow: hidden;
}
.card-svg {
  position: absolute; inset: 0;
  width: 100%; height: 100%;
  display: block;
  transition: transform 500ms cubic-bezier(0.22, 1, 0.36, 1);
}
.card:hover .card-svg { transform: scale(1.04); }
.card-body { padding: 24px; }
.tag { font-size: 11px; font-weight: 600; color: var(--color-fg-muted); letter-spacing: 0.8px; text-transform: uppercase; margin-bottom: 10px; }
.card-title { font-family: var(--font-display); font-size: 20px; font-weight: 400; line-height: 1.25; color: #000; margin-bottom: 10px; }
.card-desc { font-size: 14px; line-height: 1.6; color: var(--color-fg-secondary); letter-spacing: 0.1px; }

.cta-wrap { padding: 96px 28px; }
.cta-card {
  max-width: 760px; margin: 0 auto; background: rgba(245, 242, 239, 0.7);
  border-radius: 32px; padding: 64px 56px; box-shadow: var(--shadow-warm);
  backdrop-filter: blur(8px); text-align: center; border: 1px solid rgba(0, 0, 0, 0.04);
}
.cta-title {
  font-family: var(--font-display); font-size: clamp(28px, 4vw, 48px); font-weight: 400;
  line-height: 1.1; letter-spacing: -1px; color: #000; margin: 0 0 20px;
}
.cta-body {
  font-size: 17px; line-height: 1.65; color: var(--color-fg-secondary);
  max-width: 420px; margin: 0 auto 40px; letter-spacing: 0.1px;
}
.cta-btns { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }

@media (max-width: 900px) {
  .hero { padding-top: 48px; }
  .hero-grid, .two-col, .split, .three-grid, .tools, .cards { grid-template-columns: 1fr; gap: 40px; }
  .sticky { position: static; }
  .insights-head { flex-direction: column; align-items: flex-start; gap: 16px; }
  .tool.bordered { border-right: none; border-bottom: var(--border); }
  .section { padding-top: 72px; padding-bottom: 72px; }
  .cta-wrap { padding: 72px 20px; }
  .cta-card { padding: 48px 28px; border-radius: 24px; }
  .cta-title { font-size: clamp(26px, 7vw, 40px); }
  .cta-body { font-size: 15px; }
  .lead { font-size: 16px; margin-bottom: 24px; }
  .h2 { font-size: 28px; }
  .big-h2 { font-size: clamp(26px, 7vw, 44px); }
  .signal-word { font-size: 26px; }
}
@media (max-width: 560px) {
  .hero-grid, .two-col, .split { gap: 28px; }
  .section { padding-top: 56px; padding-bottom: 56px; }
  .three-grid { border-radius: 12px; }
  .step { padding: 24px 20px; }
  .tool { padding: 24px 4px; }
  .ctas .btn, .cta-btns .btn { flex: 1 1 auto; }
  .cta-wrap { padding: 56px 0; }
  .cta-card { padding: 40px 20px; border-radius: 20px; }
  .card-top { height: 120px; }
  .card-body { padding: 20px; }
  .insights-head h2 { font-size: 28px; }
}
</style>
