<script setup>
import { ref, onMounted, watch, nextTick } from 'vue';
import { gsap } from 'gsap';

const props = defineProps({
  n: String,
  title: String,
  body: String,
  img: Boolean,
  defaultOpen: Boolean,
});

const open = ref(!!props.defaultOpen);
const bodyEl = ref(null);
const plusEl = ref(null);

const animate = async () => {
  await nextTick();
  if (!bodyEl.value) return;
  if (open.value) {
    gsap.fromTo(
      bodyEl.value,
      { height: 0, opacity: 0 },
      { height: 'auto', opacity: 1, duration: 0.5, ease: 'power3.out' }
    );
  }
  gsap.to(plusEl.value, { rotate: open.value ? 45 : 0, duration: 0.3, ease: 'power2.out' });
};

const toggle = () => {
  if (open.value) {
    gsap.to(bodyEl.value, {
      height: 0, opacity: 0, duration: 0.35, ease: 'power2.inOut',
      onComplete: () => { open.value = false; },
    });
    gsap.to(plusEl.value, { rotate: 0, duration: 0.3, ease: 'power2.out' });
  } else {
    open.value = true;
    animate();
  }
};

onMounted(() => {
  if (open.value) animate();
});
</script>

<template>
  <div class="item">
    <button class="head" @click="toggle">
      <div class="row">
        <span class="num">{{ n }}</span>
        <span class="title">{{ title }}</span>
      </div>
      <span ref="plusEl" class="plus">+</span>
    </button>
    <div v-if="open" ref="bodyEl" class="body" style="overflow:hidden;">
      <div class="inner">
        <div v-if="img" class="thumb">
          <svg class="thumb-svg" viewBox="0 0 640 200" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
            <!-- horizontal signal rails -->
            <g stroke="#ffffff" stroke-opacity="0.08" stroke-width="1">
              <line x1="0" y1="40"  x2="640" y2="40"  />
              <line x1="0" y1="72"  x2="640" y2="72"  />
              <line x1="0" y1="104" x2="640" y2="104" />
              <line x1="0" y1="136" x2="640" y2="136" />
              <line x1="0" y1="168" x2="640" y2="168" />
            </g>

            <!-- six signal bars (varying widths → varying scores) -->
            <g fill="#ffffff">
              <rect x="80"  y="32"  width="430" height="16" rx="2" fill-opacity="0.9"  />
              <rect x="80"  y="64"  width="180" height="16" rx="2" fill-opacity="0.35" />
              <rect x="80"  y="96"  width="370" height="16" rx="2" fill-opacity="0.7"  />
              <rect x="80"  y="128" width="94"  height="16" rx="2" fill-opacity="0.25" />
              <rect x="80"  y="160" width="490" height="16" rx="2" fill-opacity="1"    />
            </g>

            <!-- signal row labels (thin caps) -->
            <g fill="#ffffff" fill-opacity="0.4">
              <rect x="36" y="38" width="28" height="4" rx="1" />
              <rect x="36" y="70" width="28" height="4" rx="1" />
              <rect x="36" y="102" width="28" height="4" rx="1" />
              <rect x="36" y="134" width="28" height="4" rx="1" />
              <rect x="36" y="166" width="28" height="4" rx="1" />
            </g>

            <!-- aggregate-score threshold -->
            <line x1="420" y1="16" x2="420" y2="184" stroke="#ffffff" stroke-opacity="0.9" stroke-width="1.5" stroke-dasharray="4 4" />
            <circle cx="420" cy="100" r="5" fill="#ffffff" />

            <!-- score chip -->
            <g transform="translate(540,20)">
              <rect x="0" y="0" width="74" height="28" rx="14" fill="#ffffff" />
              <rect x="10" y="11" width="16" height="6" rx="1" fill="#0a0a0a" />
              <rect x="30" y="8"  width="36" height="12" rx="2" fill="#0a0a0a" fill-opacity="0.2" />
            </g>
          </svg>
        </div>
        <p>{{ body }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.item { border-bottom: var(--border); }
.head {
  width: 100%; display: flex; align-items: flex-start; justify-content: space-between;
  padding: 22px 0; background: none; border: none; text-align: left; gap: 16px;
}
.row { display: flex; gap: 20px; align-items: flex-start; flex: 1; }
.num { font-size: 11px; font-weight: 500; color: var(--color-fg-faint); min-width: 24px; padding-top: 4px; }
.title { font-family: var(--font-display); font-size: 22px; font-weight: 400; color: #000; line-height: 1.2; letter-spacing: -0.2px; }
.plus { font-size: 20px; color: var(--color-fg-muted); line-height: 1; padding-top: 4px; display: inline-block; transform-origin: center; }

.body { overflow: hidden; }
.inner { padding: 0 0 28px 44px; display: flex; flex-direction: column; gap: 16px; }
.thumb {
  width: 100%; height: 200px; background: #0a0a0a; border-radius: 12px;
  margin-bottom: 8px; overflow: hidden; position: relative;
}
.thumb-svg { width: 100%; height: 100%; display: block; }
.inner p { font-size: 15px; line-height: 1.65; color: var(--color-fg-secondary); letter-spacing: 0.1px; }
</style>
