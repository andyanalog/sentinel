<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { gsap } from 'gsap';

const items = [
  'Signup fraud', 'LLM token farming', 'Credential stuffing', 'Free-tier abuse',
  'UGC spam', 'Sybil resistance', 'Airdrop farming', 'Bot management',
];

const track = ref(null);
let tween = null;

onMounted(() => {
  if (!track.value) return;
  // Two copies side-by-side for seamless loop. Animate x from 0 to -half.
  const half = track.value.scrollWidth / 2;
  tween = gsap.to(track.value, {
    x: -half,
    duration: 32,
    ease: 'none',
    repeat: -1,
  });

  track.value.addEventListener('mouseenter', () => tween.timeScale(0.25));
  track.value.addEventListener('mouseleave', () => tween.timeScale(1));
});

onBeforeUnmount(() => { if (tween) tween.kill(); });
</script>

<template>
  <div class="ticker-wrap">
    <div ref="track" class="track">
      <span v-for="(t, i) in [...items, ...items]" :key="i" class="cell">
        <span class="t">{{ t }}</span>
        <span class="dot">·</span>
      </span>
    </div>
  </div>
</template>

<style scoped>
.ticker-wrap {
  border-top: var(--border); border-bottom: var(--border);
  background: #fafafa; overflow: hidden; margin-top: 64px;
}
.track { display: flex; gap: 0; white-space: nowrap; will-change: transform; }
.cell { display: inline-flex; align-items: center; gap: 0; white-space: nowrap; }
.t {
  font-size: 12px; font-weight: 500; color: var(--color-fg-muted);
  letter-spacing: 0.8px; text-transform: uppercase; padding: 14px 24px;
}
.dot { color: rgba(0, 0, 0, 0.15); font-size: 10px; }
</style>
