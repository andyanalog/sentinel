<script setup>
defineProps({ light: Boolean });
</script>
<template>
  <div :class="['label', { light }]"><slot /></div>
</template>
<style scoped>
.label {
  font-size: 11px; font-weight: 600; letter-spacing: 1px;
  text-transform: uppercase; color: var(--color-fg-muted);
}
.label.light { color: rgba(255, 255, 255, 0.4); }
</style>
