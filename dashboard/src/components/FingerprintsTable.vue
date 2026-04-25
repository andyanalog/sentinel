<script setup lang="ts">
import ActionBadge from "./ActionBadge.vue";
import ScoreBar from "./ScoreBar.vue";
import type { FingerprintRow } from "../api";

defineProps<{ items: FingerprintRow[] }>();

function shortFp(fp: string): string {
  if (fp.length <= 18) return fp;
  return `${fp.slice(0, 10)}…${fp.slice(-6)}`;
}
</script>

<template>
  <table class="plain">
    <thead>
      <tr>
        <th>Fingerprint</th>
        <th style="width: 180px">Max score</th>
        <th style="width: 70px">Hits</th>
        <th style="width: 110px">Last</th>
        <th style="width: 140px">Seen by</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="row in items" :key="row.fingerprint">
        <td class="mono" :title="row.fingerprint">{{ shortFp(row.fingerprint) }}</td>
        <td><ScoreBar :score="row.max_score" /></td>
        <td class="mono">{{ row.hits }}</td>
        <td><ActionBadge :action="row.last_action" /></td>
        <td class="mono subtle">
          {{ row.operators.length }} op<span v-if="row.operators.length !== 1">s</span>
        </td>
      </tr>
      <tr v-if="!items.length">
        <td colspan="5" class="subtle" style="text-align: center; padding: 24px">
          No fingerprints flagged yet
        </td>
      </tr>
    </tbody>
  </table>
</template>
