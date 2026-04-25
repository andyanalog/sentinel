<script setup>
import { ref, reactive, computed, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { gsap } from 'gsap';
import Label from '../components/Label.vue';
import Footer from '../components/Footer.vue';
import HeroHeading from '../components/HeroHeading.vue';
import HeroSvg from '../components/HeroSvg.vue';
import { useReveal } from '../composables/useReveal.js';

const router = useRouter();
const root = ref(null);
useReveal(root);

const form = reactive({ name: '', email: '', company: '', usecase: '', message: '' });
const sent = ref(false);
const successRef = ref(null);

const canSend = computed(() => form.name && form.email);

const submit = async () => {
  if (!canSend.value) return;
  sent.value = true;
  await nextTick();
  if (successRef.value) {
    gsap.from(successRef.value, {
      opacity: 0, y: 16, duration: 0.7, ease: 'power3.out',
    });
    const check = successRef.value.querySelector('.check-svg path');
    if (check) {
      const len = check.getTotalLength();
      check.style.strokeDasharray = len;
      check.style.strokeDashoffset = len;
      gsap.to(check, { strokeDashoffset: 0, duration: 0.7, ease: 'power2.out', delay: 0.2 });
    }
  }
};

const blocks = [
  { label: 'API Access', body: 'Request an API key and start integrating. Includes a sandbox environment with unlimited test evaluations.' },
  { label: 'Integration support', body: 'Detailed technical guidance for your stack. Express, Fastify, Hono, or raw HTTP — we cover all of them.' },
  { label: 'Enterprise & custom', body: 'High-volume pricing, SLA discussions, on-chain customization, and dedicated support.' },
];
</script>

<template>
  <div ref="root">
    <div v-if="sent" class="success-page">
      <div ref="successRef" class="success">
        <div class="circle">
          <svg class="check-svg" width="20" height="16" viewBox="0 0 20 16" fill="none">
            <path d="M1 8l6 6L19 1" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </div>
        <h2 class="s-title">Message received.</h2>
        <p class="s-body">We'll be in touch within one business day. Most responses are faster.</p>
        <button class="btn btn-ghost btn-press" @click="router.push('/')">Back to home</button>
      </div>
    </div>

    <section v-else class="container hero">
      <div class="hero-top">
        <div class="hero-left">
          <Label>Contact</Label>
          <HeroHeading line1="Let's talk" line2="trust infrastructure." />
        </div>
        <HeroSvg variant="contact" />
      </div>
      <div class="grid">
        <div class="left">
          <p class="reveal lead">
            API access requests, integration questions, pricing discussions. We respond to everything.
          </p>

          <div class="blocks">
            <div v-for="(b, i) in blocks" :key="i" class="block reveal">
              <div class="num">0{{ i + 1 }}</div>
              <div>
                <div class="b-title">{{ b.label }}</div>
                <p class="b-body">{{ b.body }}</p>
              </div>
            </div>
          </div>
        </div>

        <form class="form reveal" @submit.prevent="submit">
          <div class="two">
            <div class="field">
              <label>Name</label>
              <input v-model="form.name" placeholder="Alex Chen" />
            </div>
            <div class="field">
              <label>Email</label>
              <input v-model="form.email" type="email" placeholder="alex@company.com" />
            </div>
          </div>
          <div class="field">
            <label>Company</label>
            <input v-model="form.company" placeholder="Acme Inc." />
          </div>
          <div class="field">
            <label>Use case</label>
            <select v-model="form.usecase" :class="{ placeholder: !form.usecase }">
              <option value="">Select a use case</option>
              <option>Signup / account creation</option>
              <option>LLM / AI inference API</option>
              <option>Login / authentication</option>
              <option>Free-tier SaaS abuse</option>
              <option>UGC / comment spam</option>
              <option>Web3 faucet / airdrop</option>
              <option>Other</option>
            </select>
          </div>
          <div class="field">
            <label>Tell us more</label>
            <textarea v-model="form.message" placeholder="What are you building? What does your abuse pattern look like today?" />
          </div>
          <button type="submit" class="btn btn-primary btn-press" :disabled="!canSend" :class="{ disabled: !canSend }">
            Send message
          </button>
          <div class="foot">We respond within one business day.</div>
        </form>
      </div>
    </section>

    <Footer v-if="!sent" />
  </div>
</template>

<style scoped>
.hero { padding-top: 60px; padding-bottom: 80px; }
.hero-top { display: grid; grid-template-columns: 1fr 1fr; gap: 64px; align-items: center; margin-bottom: 64px; }
.hero-top > * { min-width: 0; }
.hero-top .hero-left { display: flex; flex-direction: column; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 80px; align-items: start; }
.left { display: flex; flex-direction: column; }
.lead { font-size: 17px; line-height: 1.65; color: var(--color-fg-secondary); margin: 0 0 48px; letter-spacing: 0.1px; max-width: 400px; }

.blocks { display: flex; flex-direction: column; gap: 28px; }
.block { display: flex; gap: 20px; align-items: flex-start; padding-bottom: 28px; border-bottom: var(--border); }
.num {
  width: 32px; height: 32px; background: #f5f5f5; border-radius: 8px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  font-size: 11px; font-weight: 700; color: var(--color-fg-muted);
}
.b-title { font-size: 15px; font-weight: 600; color: #000; margin-bottom: 6px; letter-spacing: 0.1px; }
.b-body { font-size: 14px; line-height: 1.65; color: var(--color-fg-secondary); letter-spacing: 0.1px; }

.form {
  background: #fff; border-radius: 24px; padding: 40px;
  box-shadow: var(--shadow-card); border: 1px solid rgba(0, 0, 0, 0.05);
  display: flex; flex-direction: column; gap: 20px;
}
.two { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.field { display: flex; flex-direction: column; gap: 6px; }
.field label { font-size: 13px; font-weight: 500; color: #000; letter-spacing: 0.1px; }
.field input, .field select, .field textarea {
  width: 100%; font-size: 15px; padding: 11px 14px;
  border-radius: 8px; border: 1px solid #e5e5e5; outline: none;
  color: #000; background: #fff; letter-spacing: 0.1px;
  transition: border-color 180ms ease, box-shadow 180ms ease;
}
.field input:focus, .field select:focus, .field textarea:focus {
  border-color: rgba(0, 0, 0, 0.25);
  box-shadow: rgba(147, 197, 253, 0.4) 0px 0px 0px 3px;
}
.field textarea { min-height: 120px; resize: vertical; font-family: inherit; }
.field select.placeholder { color: var(--color-fg-faint); }

.btn { display: inline-flex; align-items: center; justify-content: center; border: none; font-weight: 600; letter-spacing: 0.1px; font-size: 14px; }
.btn-primary { background: #000; color: #fff; padding: 13px; border-radius: 9999px; transition: opacity 150ms ease; }
.btn-primary:hover { opacity: 0.85; }
.btn-primary.disabled { opacity: 0.4; cursor: not-allowed; }
.btn-ghost { background: none; color: #000; padding: 10px 20px; border-radius: 9999px; border: 1px solid rgba(0, 0, 0, 0.15); font-weight: 500; }
.btn-ghost:hover { background: rgba(0, 0, 0, 0.04); }

.foot { font-size: 12px; color: var(--color-fg-muted); text-align: center; letter-spacing: 0.1px; }

.success-page {
  min-height: calc(100vh - 60px); display: flex; align-items: center; justify-content: center;
  padding: 0 24px;
}
.success { text-align: center; max-width: 440px; }
.circle {
  width: 48px; height: 48px; background: #000; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; margin: 0 auto 24px;
}
.s-title { font-family: var(--font-display); font-size: 36px; font-weight: 400; color: #000; margin: 0 0 16px; letter-spacing: -0.6px; }
.s-body { font-size: 16px; line-height: 1.65; color: var(--color-fg-secondary); margin: 0 0 32px; letter-spacing: 0.1px; }

@media (max-width: 900px) {
  .hero { padding-top: 32px; padding-bottom: 48px; }
  .hero-top { grid-template-columns: 1fr; gap: 32px; margin-bottom: 40px; }
  .grid { grid-template-columns: 1fr; gap: 48px; }
  .two { grid-template-columns: 1fr 1fr; gap: 14px; }
  .lead { font-size: 16px; margin: 20px 0 36px; }
  .form { padding: 28px; border-radius: 20px; }
  .s-title { font-size: clamp(26px, 7vw, 32px); }
}
@media (max-width: 420px) {
  .two { grid-template-columns: 1fr; }
  .form { padding: 22px; }
}
</style>
