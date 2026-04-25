<script setup lang="ts">
defineProps<{
  label: string;
  value: string | number;
  hint?: string;
  tone?: "default" | "allow" | "challenge" | "block";
}>();
</script>

<template>
  <div class="card">
    <h2>{{ label }}</h2>
    <div
      class="kpi-value"
      :style="{
        color:
          tone === 'block'
            ? 'var(--red)'
            : tone === 'challenge'
            ? 'var(--amber)'
            : tone === 'allow'
            ? 'var(--green)'
            : 'var(--fg)',
      }"
    >
      {{ value }}
    </div>
    <div v-if="hint" class="kpi-delta">{{ hint }}</div>
  </div>
</template>
