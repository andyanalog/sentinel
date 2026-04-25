<script setup lang="ts">
import type { Action } from "../api";

defineProps<{ action: Action }>();

const cls: Record<Action, string> = {
  ALLOW: "badge badge-allow",
  CHALLENGE: "badge badge-challenge",
  BLOCK: "badge badge-block",
};
</script>

<template>
  <span :class="cls[action]">
    <span class="badge-dot" />
    {{ action }}
  </span>
</template>
