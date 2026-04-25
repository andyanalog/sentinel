<script setup>
import { ref, onMounted } from 'vue';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

const signals = [
  { label: 'Request cadence',   val: 82, color: '#dc2626' },
  { label: 'Endpoint diversity', val: 34, color: '#16a34a' },
  { label: 'IP reputation',      val: 71, color: '#d97706' },
  { label: 'Error rate',         val: 18, color: '#16a34a' },
  { label: 'Cross-op history',   val: 94, color: '#dc2626' },
  { label: 'ASN reputation',     val: 55, color: '#d97706' },
];

const root = ref(null);
const scoreLabel = ref(null);
const bars = ref([]);

onMounted(() => {
  const tl = gsap.timeline({
    scrollTrigger: { trigger: root.value, start: 'top 80%' },
  });

  // Card intro
  tl.from(root.value, { y: 20, opacity: 0, duration: 0.7, ease: 'power3.out' });

  // Bars: width sweep
  bars.value.forEach((bar, i) => {
    const v = signals[i].val;
    tl.fromTo(
      bar,
      { width: '0%' },
      { width: `${v}%`, duration: 0.8, ease: 'power3.out' },
      0.2 + i * 0.08
    );
  });

  // Score counter
  const obj = { val: 0 };
  tl.to(
    obj,
    {
      val: 78,
      duration: 1.4,
      ease: 'power2.out',
      onUpdate: () => {
        if (scoreLabel.value) scoreLabel.value.textContent = `BLOCK · Score ${Math.round(obj.val)}`;
      },
    },
    0.3
  );
});
</script>

<template>
  <div ref="root" class="card">
    <div class="head">
      <div class="title">Signal breakdown</div>
      <div class="status">
        <div class="dot" />
        <div ref="scoreLabel" class="score">BLOCK · Score 0</div>
      </div>
    </div>

    <div v-for="(s, i) in signals" :key="s.label" class="row">
      <div class="meta">
        <span class="lbl">{{ s.label }}</span>
        <span class="val" :style="{ color: s.color }">{{ s.val }}</span>
      </div>
      <div class="track">
        <div
          :ref="(el) => (bars[i] = el)"
          class="bar"
          :style="{ background: s.color, width: '0%' }"
        />
      </div>
    </div>

    <div class="note">
      <div class="note-dot" />
      <div class="note-text">Fingerprint previously flagged on 4 other APIs. Cross-operator EMA: 0.82.</div>
    </div>
  </div>
</template>

<style scoped>
.card {
  background: #fff; border-radius: 16px; padding: 24px;
  box-shadow: var(--shadow-card); border: 1px solid rgba(0, 0, 0, 0.05);
}
.head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.title { font-size: 13px; font-weight: 600; color: #000; letter-spacing: 0.1px; }
.status { display: flex; gap: 6px; align-items: center; }
.dot { width: 8px; height: 8px; border-radius: 50%; background: #dc2626; box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.6); animation: pulse 1.8s infinite; }
@keyframes pulse {
  0%   { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.55); }
  70%  { box-shadow: 0 0 0 10px rgba(220, 38, 38, 0); }
  100% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0); }
}
.score { font-size: 12px; font-weight: 700; color: #dc2626; }

.row { margin-bottom: 12px; }
.meta { display: flex; justify-content: space-between; margin-bottom: 5px; }
.lbl { font-size: 12px; color: var(--color-fg-muted); }
.val { font-size: 12px; font-weight: 600; }
.track { height: 3px; background: #f0f0f0; border-radius: 99px; overflow: hidden; }
.bar { height: 3px; border-radius: 99px; }

.note {
  margin-top: 20px; padding: 10px 14px; background: #fef2f2; border-radius: 8px;
  display: flex; gap: 10px; align-items: center;
}
.note-dot { width: 6px; height: 6px; border-radius: 50%; background: #dc2626; flex-shrink: 0; }
.note-text { font-size: 12px; color: #991b1b; line-height: 1.4; }
</style>
