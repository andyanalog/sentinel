<script setup lang="ts">
import { computed } from "vue";

import ActionBadge from "./ActionBadge.vue";
import ScoreBar from "./ScoreBar.vue";
import type { EvalEvent } from "../api";

const props = defineProps<{ events: EvalEvent[] }>();

function fmtTime(ts: number): string {
  const d = new Date(ts * 1000);
  return d.toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function shortFp(fp: string): string {
  if (fp.length <= 14) return fp;
  return `${fp.slice(0, 8)}…${fp.slice(-4)}`;
}

function topSignals(signals: Record<string, number>): [string, number][] {
  return Object.entries(signals)
    .filter(([, v]) => v > 0)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 3);
}

const rows = computed(() => props.events);
</script>

<template>
  <table class="plain">
    <thead>
      <tr>
        <th style="width: 88px">Time</th>
        <th style="width: 110px">Action</th>
        <th style="width: 180px">Score</th>
        <th>Fingerprint</th>
        <th>Top signals</th>
        <th style="width: 140px">Operator</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="e in rows" :key="e.eval_id">
        <td class="mono subtle">{{ fmtTime(e.ts) }}</td>
        <td><ActionBadge :action="e.action" /></td>
        <td><ScoreBar :score="e.score" /></td>
        <td class="mono" :title="e.fingerprint">{{ shortFp(e.fingerprint) }}</td>
        <td class="mono subtle">
          <span
            v-for="([name, val], i) in topSignals(e.signals)"
            :key="name"
          >
            {{ name }}={{ val.toFixed(2)
            }}<span v-if="i < topSignals(e.signals).length - 1">, </span>
          </span>
        </td>
        <td class="mono subtle">{{ e.operator_id }}</td>
      </tr>
      <tr v-if="!rows.length">
        <td colspan="6" class="subtle" style="text-align: center; padding: 32px">
          No evaluations yet — send a request to /v1/evaluate
        </td>
      </tr>
    </tbody>
  </table>
</template>
