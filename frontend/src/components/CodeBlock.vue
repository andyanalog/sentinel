<script setup>
import { ref, onMounted } from 'vue';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

const root = ref(null);
onMounted(() => {
  // Typed-cursor feel: subtle reveal + faint glow when it enters view.
  gsap.fromTo(
    root.value,
    { opacity: 0, y: 18, filter: 'blur(6px)' },
    {
      opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.9, ease: 'power3.out',
      scrollTrigger: { trigger: root.value, start: 'top 85%' },
    }
  );
});
</script>

<template>
  <div ref="root" class="code">
    <div class="bar"><span /><span /><span /></div>
    <pre><slot /></pre>
  </div>
</template>

<style scoped>
.code {
  background: #0a0a0a; border-radius: 12px; padding: 0;
  overflow: hidden;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.18);
  max-width: 100%;
  min-width: 0;
}
.bar { display: flex; gap: 6px; padding: 12px 16px; border-bottom: 1px solid rgba(255, 255, 255, 0.06); }
.bar span { width: 10px; height: 10px; border-radius: 50%; background: #262626; }
.bar span:nth-child(1) { background: #3d3d3d; }
.bar span:nth-child(2) { background: #2e2e2e; }
.bar span:nth-child(3) { background: #252525; }
pre {
  margin: 0; padding: 22px 26px; overflow-x: auto;
  font-family: var(--font-mono); font-size: 13px; line-height: 1.8;
  color: #e5e5e5; white-space: pre;
}
</style>
