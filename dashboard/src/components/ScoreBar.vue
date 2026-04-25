<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{ score: number }>();

const color = computed(() => {
  if (props.score >= 65) return "var(--red)";
  if (props.score >= 40) return "var(--amber)";
  return "var(--green)";
});
</script>

<template>
  <div style="display: flex; align-items: center; gap: 10px; min-width: 160px">
    <div class="score-bar" style="flex: 1">
      <div
        class="score-bar-fill"
        :style="{ width: Math.max(2, score) + '%', background: color }"
      />
    </div>
    <span class="mono" :style="{ color, minWidth: '24px', textAlign: 'right' }">
      {{ score }}
    </span>
  </div>
</template>
