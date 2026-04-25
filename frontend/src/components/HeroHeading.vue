<script setup>
import { ref, onMounted, computed } from 'vue';
import { gsap } from 'gsap';

const props = defineProps({
  line1: { type: String, required: true },
  line2: { type: String, required: true },
});

const root = ref(null);

const toWords = (s) =>
  s.split(/(\s+)/).filter(Boolean).map((token) => ({
    isSpace: /^\s+$/.test(token),
    chars: Array.from(token),
  }));

const words1 = computed(() => toWords(props.line1));
const words2 = computed(() => toWords(props.line2));

onMounted(() => {
  const chars = root.value.querySelectorAll('.split-char');
  gsap.to(chars, {
    y: '0%',
    opacity: 1,
    duration: 0.9,
    stagger: 0.02,
    ease: 'power4.out',
    delay: 0.15,
  });
});
</script>

<template>
  <h1 ref="root" class="hero">
    <span class="line">
      <template v-for="(w, i) in words1" :key="'a' + i">
        <span v-if="w.isSpace" class="space">&nbsp;</span>
        <span v-else class="split-word">
          <span v-for="(c, j) in w.chars" :key="j" class="split-char">{{ c }}</span>
        </span>
      </template>
    </span>
    <em class="line italic">
      <template v-for="(w, i) in words2" :key="'b' + i">
        <span v-if="w.isSpace" class="space">&nbsp;</span>
        <span v-else class="split-word">
          <span v-for="(c, j) in w.chars" :key="j" class="split-char">{{ c }}</span>
        </span>
      </template>
    </em>
  </h1>
</template>

<style scoped>
.hero {
  font-family: var(--font-display);
  font-size: clamp(40px, 6vw, 88px);
  font-weight: 400;
  line-height: 1.12;
  letter-spacing: -1.5px;
  color: #000;
  margin: 20px 0 0;
  padding-bottom: 0.12em;
  text-align: left;
}
@media (max-width: 560px) {
  .hero { letter-spacing: -1px; }
}

/* Each .line is its own block — forces identical left edge across lines. */
.line {
  display: block;
  font-style: normal;
}
.italic {
  font-style: italic;
  color: var(--color-fg-muted);
  /* Compensate for italic glyph side-bearing so line-2 starts
     visually flush-left with line-1 (DM Serif Italic first-glyph
     left bearing is larger than the roman). */
  margin-left: -0.035em;
}

.space {
  display: inline-block;
  white-space: pre;
  vertical-align: baseline;
}
.split-word {
  display: inline-block;
  white-space: nowrap;
  vertical-align: baseline;
  padding-bottom: 0.15em;
}
.split-char {
  display: inline-block;
  transform: translate3d(0, 40%, 0);
  opacity: 0;
  will-change: transform, opacity;
}
</style>
