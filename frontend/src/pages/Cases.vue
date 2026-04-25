<script setup>
import { ref, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { gsap } from 'gsap';
import Label from '../components/Label.vue';
import Divider from '../components/Divider.vue';
import Footer from '../components/Footer.vue';
import HeroHeading from '../components/HeroHeading.vue';
import HeroSvg from '../components/HeroSvg.vue';
import { useReveal } from '../composables/useReveal.js';

const router = useRouter();
const root = ref(null);
const active = ref(0);
const detailEl = ref(null);

useReveal(root);

const cases = [
  {
    tag: 'Signup fraud',
    title: 'Fake account farms on registration endpoints',
    headline: 'From CAPTCHA at submit to behavioral scoring across every route.',
    body: "The incumbent answer is Cloudflare Turnstile or hCaptcha — widgets that fire once at form submit and can't see behavior across your other routes. Sentinel evaluates every request, carries reputation across endpoints (signup → first login → first write), and costs cents per thousand instead of a Turnstile Enterprise contract.",
    comparison: 'Better fit when your abuse signal shows up after signup — burst API calls from a newly-created account. Sentinel catches the pattern before it becomes a problem.',
    signal: 'BLOCK',
    metrics: ['< $0.001 per evaluation', 'Cross-endpoint reputation', 'Zero user-visible friction', 'Catches post-signup abuse patterns'],
    color: '#1a1a1a',
  },
  {
    tag: 'AI inference',
    title: 'LLM APIs under scraper and token-farming pressure',
    headline: 'A scraper burning free tiers on competitor A is pre-flagged when it hits you.',
    body: 'OpenAI-wrapper products get hammered by actors cycling free-tier keys to resell inference. Rate-limiting by API key is trivially bypassed; rate-limiting by IP punishes legitimate shared-NAT users. Sentinel fingerprints across key+IP+ASN+cadence and shares the reputation with every other LLM wrapper on the network.',
    comparison: "Cloudflare Bot Management can do per-site rate limits but not cross-tenant reputation. Sentinel's cross-operator ledger is the differentiator.",
    signal: 'BLOCK',
    metrics: ['Cross-tenant fingerprint matching', 'Key + IP + ASN + cadence signal', 'Pre-flagged before first request lands', 'No shared-NAT false positives'],
    color: '#0f172a',
  },
  {
    tag: 'Auth security',
    title: 'Credential stuffing on login endpoints',
    headline: 'Sentinel sees the botnet hitting twelve login endpoints simultaneously. Block on request one.',
    body: "Auth0/Okta anomaly detection and Stytch device intelligence work, but they're priced for enterprise SSO ($0.02–$0.25 per MAU) and only see your tenant's traffic. Sentinel sees the same credential-stuffing botnet hitting a dozen other login endpoints simultaneously and blocks it on request 1, not request 100.",
    comparison: 'Pay-per-eval pricing means a hobbyist auth flow can afford the same signal quality as a funded startup. No per-MAU fee.',
    signal: 'BLOCK',
    metrics: ['Block on request 1, not request 100', 'Cross-tenant botnet visibility', 'Pay-per-eval (not per MAU)', 'Same signal quality at any scale'],
    color: '#1c1917',
  },
  {
    tag: 'SaaS',
    title: 'Free-tier abuse on developer and SaaS APIs',
    headline: 'Image generation, email sending, code execution — anywhere free tier depends on abuse staying low.',
    body: 'Castle.io and Arkose Labs solve this but require 6-figure ACVs and enterprise sales cycles. Sentinel gives you the same ALLOW/CHALLENGE/BLOCK decision for a fraction of a cent per call with an afternoon of integration. No enterprise contract, no minimum commit.',
    comparison: 'The CHALLENGE signal routes to your preferred step-up — email verification, CAPTCHA, or manual review. Sentinel decides; you own the UX.',
    signal: 'CHALLENGE',
    metrics: ['Fractions of a cent per call', 'Afternoon integration, not weeks', 'No enterprise contract or ACV', 'CHALLENGE routes to your step-up UX'],
    color: '#292524',
  },
  {
    tag: 'Content',
    title: 'Review, comment, and UGC spam rings',
    headline: 'Cross-app signal catches coordinated spam before the content-level classifier sees the payload.',
    body: "Akismet works for WordPress-shaped content but is blind to the upstream request pattern — the same fingerprint posting to ten unrelated sites in a minute. Sentinel's cross-app signal catches coordinated spam rings before the content-level classifier sees the payload, which is strictly cheaper than running an LLM moderation pass on garbage.",
    comparison: 'Cheaper than an LLM moderation pass on every post. Catches the pattern at the request layer, before content exists.',
    signal: 'BLOCK',
    metrics: ['Request-layer detection before content exists', 'Cross-site spam ring visibility', 'Cheaper than LLM moderation on junk', 'Works with any content type'],
    color: '#1e1b4b',
  },
  {
    tag: 'Web3',
    title: 'Crypto faucets, airdrop claims, and quest platforms',
    headline: 'Sybil resistance that runs silently. Zero user enrollment required.',
    body: "Gitcoin Passport and Worldcoin solve identity but require the user to actively enroll; most faucet users won't. Sentinel runs silently in the request path, flags the same wallet-farming fingerprint across every faucet on the network, and settles its own fees in the same USDC the faucet is already handling.",
    comparison: 'Natural fit: onchain product, onchain payment rail, onchain reputation ledger. No credential friction for legitimate claimants.',
    signal: 'BLOCK',
    metrics: ['Zero user enrollment friction', 'Cross-faucet Sybil fingerprinting', 'USDC settlement on Arc L1', 'Works for any quest or claim flow'],
    color: '#042f2e',
  },
];

const select = async (i) => {
  if (i === active.value) return;
  active.value = i;
  await nextTick();
  if (detailEl.value) {
    gsap.fromTo(
      detailEl.value,
      { opacity: 0, y: 12 },
      { opacity: 1, y: 0, duration: 0.5, ease: 'power3.out' }
    );
  }
};

const signalColor = (s) =>
  s === 'BLOCK' ? '#ef4444' : s === 'CHALLENGE' ? '#f59e0b' : '#22c55e';
const signalTint = (s) =>
  s === 'BLOCK' ? '#fca5a5' : s === 'CHALLENGE' ? '#fde68a' : '#86efac';

const ipNotes = [
  { title: 'ASN reputation survives rotation', body: 'When IP flips, the ASN stays. ASN-level reputation and the coarser prior still fire on the new address.' },
  { title: 'Behavioral signals catch fast', body: "Cadence and endpoint-diversity signals don't need history. A first burst from a new fingerprint triggers CHALLENGE in seconds." },
  { title: 'Non-IP components are sticky', body: "User-agent, accept-language, and header ordering persist across IP rotations — the fingerprint isn't purely IP-derived." },
  { title: 'Raise cost, not block everything', body: 'The goal is to raise the cost of abuse. A rotating-IP attacker pays friction every 24h; a legitimate user lands back in ALLOW after 1–2 low-risk requests.' },
];
</script>

<template>
  <div ref="root">
    <section class="hero container">
      <div class="hero-grid">
        <div class="hero-left">
          <Label>Case studies</Label>
          <HeroHeading line1="Fresh insights &amp;" line2="chain-level walkthroughs." />
        </div>
        <HeroSvg variant="cases" />
      </div>
      <Divider />
    </section>

    <section class="container browser-wrap">
      <div class="browser reveal">
        <div class="sidebar">
          <button
            v-for="(c, i) in cases"
            :key="i"
            :class="['tab', { active: active === i }]"
            @click="select(i)"
          >
            <div class="tab-tag">{{ c.tag }}</div>
            <div class="tab-title">{{ c.title }}</div>
          </button>
        </div>
        <div ref="detailEl" class="detail">
          <div class="detail-head" :style="{ background: cases[active].color }">
            <div class="sig-row">
              <div class="sig-dot" :style="{ background: signalColor(cases[active].signal) }" />
              <span class="sig-label" :style="{ color: signalTint(cases[active].signal) }">{{ cases[active].signal }}</span>
            </div>
            <h2 class="sig-head">{{ cases[active].headline }}</h2>
          </div>
          <div class="detail-body">
            <div>
              <div class="block-lbl">The problem</div>
              <p class="block-body">{{ cases[active].body }}</p>
            </div>
            <div>
              <div class="block-lbl">Why Sentinel fits</div>
              <p class="block-body">{{ cases[active].comparison }}</p>
            </div>
            <div>
              <div class="block-lbl">Key signals</div>
              <div class="metrics">
                <div v-for="(m, i) in cases[active].metrics" :key="i" class="metric">
                  <div class="m-dot" />
                  <span>{{ m }}</span>
                </div>
              </div>
            </div>
            <div>
              <button class="btn btn-primary btn-press" @click="router.push('/contact')">
                Talk to us about this use case
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <div class="grey-band">
      <section class="container ip-section">
        <div class="ip-grid">
          <div class="reveal">
            <Label>A note on rotating IPs</Label>
            <div class="ip-title">Probabilistic, not a perfect bouncer.</div>
          </div>
          <div class="ip-items">
            <div v-for="(n, i) in ipNotes" :key="i" class="ip-item reveal">
              <div class="ip-item-title">{{ n.title }}</div>
              <p class="ip-item-body">{{ n.body }}</p>
            </div>
          </div>
        </div>
      </section>
    </div>

    <section class="end-cta">
      <h2 class="end-h2 reveal">Your use case isn't listed?</h2>
      <p class="end-p reveal">If you have an API, we probably fit. Tell us what you're building.</p>
      <button class="btn btn-primary btn-press reveal" @click="router.push('/contact')">Talk to us</button>
    </section>

    <Footer />
  </div>
</template>

<style scoped>
.hero { padding-top: 80px; padding-bottom: 0; }
.hero-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 64px; align-items: center; margin-bottom: 56px; }
.hero-grid > * { min-width: 0; }
.hero-left { display: flex; flex-direction: column; }
@media (max-width: 900px) {
  .hero-grid { grid-template-columns: 1fr; gap: 32px; margin-bottom: 32px; }
}

.browser-wrap { padding-top: 64px; padding-bottom: 64px; }
.browser {
  display: grid; grid-template-columns: 280px 1fr; gap: 0;
  border: var(--border); border-radius: 20px; overflow: hidden;
}
.sidebar { border-right: var(--border); background: #fafafa; }
.tab {
  width: 100%; text-align: left; padding: 20px 24px;
  background: transparent; border: none; border-bottom: var(--border);
  border-left: 2px solid transparent;
  transition: background 150ms ease, border-color 180ms ease;
}
.tab:hover { background: rgba(0, 0, 0, 0.02); }
.tab.active { background: #fff; border-left-color: #000; }
.tab-tag { font-size: 11px; font-weight: 600; color: var(--color-fg-muted); letter-spacing: 0.8px; text-transform: uppercase; margin-bottom: 6px; }
.tab-title { font-size: 14px; font-weight: 500; color: var(--color-fg-secondary); line-height: 1.4; letter-spacing: 0.1px; }
.tab.active .tab-title { color: #000; }

.detail { display: flex; flex-direction: column; }
.detail-head { padding: 40px 48px; min-height: 200px; display: flex; flex-direction: column; justify-content: flex-end; gap: 12px; }
.sig-row { display: flex; gap: 8px; align-items: center; }
.sig-dot { width: 8px; height: 8px; border-radius: 50%; }
.sig-label { font-size: 11px; font-weight: 700; letter-spacing: 1px; }
.sig-head { font-family: var(--font-display); font-size: 28px; font-weight: 400; line-height: 1.2; color: #fff; letter-spacing: -0.4px; max-width: 560px; }

.detail-body { padding: 40px 48px; display: flex; flex-direction: column; gap: 28px; }
.block-lbl { font-size: 11px; font-weight: 600; color: var(--color-fg-muted); letter-spacing: 0.8px; text-transform: uppercase; margin-bottom: 12px; }
.block-body { font-size: 16px; line-height: 1.7; color: var(--color-fg-secondary); letter-spacing: 0.1px; }
.metrics { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.metric { display: flex; gap: 10px; align-items: flex-start; padding: 12px 16px; background: #f5f5f5; border-radius: 8px; transition: background 200ms ease; }
.metric:hover { background: #eceae4; }
.m-dot { width: 4px; height: 4px; background: #000; border-radius: 50%; margin-top: 7px; flex-shrink: 0; }
.metric span { font-size: 13px; line-height: 1.5; color: var(--color-fg-secondary); letter-spacing: 0.1px; }

.btn { display: inline-flex; align-items: center; justify-content: center; border: none; font-weight: 600; letter-spacing: 0.1px; }
.btn-primary { background: #000; color: #fff; padding: 10px 22px; border-radius: 9999px; font-size: 13px; }
.btn-primary:hover { opacity: 0.85; }

.grey-band { background: #f5f5f5; border-top: var(--border); border-bottom: var(--border); }
.ip-section { padding-top: 64px; padding-bottom: 64px; }
.ip-grid { display: grid; grid-template-columns: 240px 1fr; gap: 64px; }
.ip-title { font-family: var(--font-display); font-size: 22px; font-weight: 400; line-height: 1.2; color: #000; margin: 12px 0; letter-spacing: -0.2px; }
.ip-items { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
.ip-item { display: flex; flex-direction: column; gap: 8px; }
.ip-item-title { font-size: 14px; font-weight: 600; color: #000; letter-spacing: 0.1px; }
.ip-item-body { font-size: 14px; line-height: 1.65; color: var(--color-fg-secondary); letter-spacing: 0.1px; }

.end-cta { padding: 80px 28px; text-align: center; }
.end-h2 { font-family: var(--font-display); font-size: 36px; font-weight: 400; color: #000; margin: 0 0 20px; letter-spacing: -0.6px; }
.end-p { font-size: 16px; color: var(--color-fg-secondary); line-height: 1.65; max-width: 400px; margin: 0 auto 32px; letter-spacing: 0.1px; }
.btn.btn-primary.btn-press { padding: 12px 28px; font-size: 14px; }

@media (max-width: 900px) {
  .hero { padding-top: 48px; }
  .browser-wrap { padding-top: 40px; padding-bottom: 40px; }
  .browser, .ip-grid, .ip-items, .metrics { grid-template-columns: 1fr; gap: 20px; }
  .ip-grid { gap: 28px; }
  .sidebar {
    border-right: none; border-bottom: var(--border);
    display: flex; overflow-x: auto; scrollbar-width: none;
  }
  .sidebar::-webkit-scrollbar { display: none; }
  .tab {
    min-width: 220px; border-bottom: none;
    border-right: var(--border);
    border-left: none;
    border-top: 2px solid transparent;
  }
  .tab.active { border-left: none; border-top-color: #000; }
  .detail-head { padding: 32px 24px; min-height: 160px; }
  .sig-head { font-size: 22px; }
  .detail-body { padding: 32px 24px; gap: 24px; }
  .block-body { font-size: 15px; }
  .ip-section { padding-top: 48px; padding-bottom: 48px; }
  .ip-title { font-size: 20px; }
  .end-h2 { font-size: clamp(26px, 7vw, 32px); }
  .end-cta { padding: 56px 0; }
}
@media (max-width: 560px) {
  .detail-head { padding: 24px 20px; }
  .detail-body { padding: 24px 20px; }
  .metric { padding: 10px 12px; }
}
</style>
