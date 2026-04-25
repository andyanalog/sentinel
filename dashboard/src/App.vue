<script setup lang="ts">
import { computed, ref } from "vue";

import { api } from "./api";
import { usePoll } from "./composables/usePoll";
import EventsTable from "./components/EventsTable.vue";
import FingerprintsTable from "./components/FingerprintsTable.vue";
import Kpi from "./components/Kpi.vue";
import OperatorsTable from "./components/OperatorsTable.vue";
import TimelineChart from "./components/TimelineChart.vue";

interface Range {
  label: string;
  window: number;  // total seconds shown
  bucket: number;  // seconds per bucket
}
const ranges: Range[] = [
  { label: "1m",  window: 60,   bucket: 2 },
  { label: "5m",  window: 300,  bucket: 5 },
  { label: "15m", window: 900,  bucket: 15 },
  { label: "1h",  window: 3600, bucket: 60 },
];
const range = ref<Range>(ranges[1]);

const health = usePoll(() => api.health(), 5000);
const eventsData = usePoll(() => api.events(100), 1200);
const fps = usePoll(() => api.fingerprints(8), 2500);
const ops = usePoll(() => api.operators(), 2500);
// Poll the chart exactly once per bucket interval. Finer polling is pointless
// — bucket edges are clock-aligned on the backend, so sub-bucket polls would
// just redraw the same grid with the same numbers. Matching the poll to the
// bucket is what makes the chart feel "calm" (Conviva / Datadog style)
// instead of sliding every second.
const series = usePoll(
  () => api.timeseries(range.value.window, range.value.bucket),
  // Clamp so very coarse ranges (1h / 60s buckets) still refresh often
  // enough that the in-progress bucket visibly grows.
  Math.min(15000, Math.max(1000, range.value.bucket * 1000)),
);

const counts = computed(
  () =>
    eventsData.data.value?.counts ?? { ALLOW: 0, CHALLENGE: 0, BLOCK: 0 },
);
const total = computed(
  () => counts.value.ALLOW + counts.value.CHALLENGE + counts.value.BLOCK,
);
const blockRate = computed(() => {
  if (!total.value) return "0.0%";
  return ((counts.value.BLOCK / total.value) * 100).toFixed(1) + "%";
});

const healthy = computed(() => health.data.value?.status === "ok");
const mode = computed(() =>
  health.data.value?.dummy_mode ? "dummy" : "production",
);
</script>

<template>
  <div style="max-width: 1280px; margin: 0 auto; padding: 32px 24px 64px">
    <header
      style="
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 32px;
      "
    >
      <div style="display: flex; align-items: center; gap: 12px">
        <div
          style="
            width: 28px;
            height: 28px;
            border-radius: 8px;
            background: #0a0a0a;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 14px;
            letter-spacing: -0.02em;
          "
        >
          S
        </div>
        <div>
          <div style="font-weight: 600; letter-spacing: -0.02em">Sentinel</div>
          <div class="subtle" style="font-size: 0.75rem">
            Trust-as-a-Service
          </div>
        </div>
      </div>

      <div style="display: flex; align-items: center; gap: 16px">
        <span
          class="mono subtle"
          style="font-size: 0.75rem"
        >
          mode: {{ mode }}
        </span>
        <span style="display: inline-flex; align-items: center; gap: 8px">
          <span
            class="status-dot"
            :class="{ offline: !healthy }"
          />
          <span style="font-size: 0.8125rem">
            {{ healthy ? "online" : "offline" }}
          </span>
        </span>
      </div>
    </header>

    <section
      style="
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 16px;
        margin-bottom: 24px;
      "
    >
      <Kpi label="Total evaluations" :value="total.toLocaleString()" />
      <Kpi
        label="Allowed"
        :value="counts.ALLOW.toLocaleString()"
        tone="allow"
      />
      <Kpi
        label="Challenged"
        :value="counts.CHALLENGE.toLocaleString()"
        tone="challenge"
      />
      <Kpi
        label="Blocked"
        :value="counts.BLOCK.toLocaleString()"
        tone="block"
        :hint="`${blockRate} block rate`"
      />
    </section>

    <section style="margin-bottom: 16px">
      <div class="card" style="padding: 0">
        <div
          style="
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 16px 20px;
            border-bottom: 1px solid var(--border);
          "
        >
          <div>
            <div style="font-weight: 500">Traffic over time</div>
            <div class="subtle" style="font-size: 0.8125rem">
              Allowed / challenged / blocked per {{ range.bucket }}s bucket
              · avg score overlay
            </div>
          </div>
          <div style="display: flex; gap: 4px">
            <button
              v-for="r in ranges"
              :key="r.label"
              class="ghost"
              :style="{
                borderColor:
                  range.label === r.label ? '#0a0a0a' : 'var(--border)',
                background:
                  range.label === r.label ? '#0a0a0a' : 'transparent',
                color: range.label === r.label ? '#fff' : 'var(--fg)',
              }"
              @click="range = r"
            >
              {{ r.label }}
            </button>
          </div>
        </div>
        <div style="padding: 16px 20px 8px">
          <div
            style="
              display: flex;
              gap: 18px;
              font-size: 0.75rem;
              color: var(--fg-muted);
              margin-bottom: 8px;
            "
          >
            <span style="display: inline-flex; align-items: center; gap: 6px">
              <span
                style="
                  width: 10px;
                  height: 3px;
                  background: #0a7d3a;
                  border-radius: 2px;
                "
              />
              Allowed
            </span>
            <span style="display: inline-flex; align-items: center; gap: 6px">
              <span
                style="
                  width: 10px;
                  height: 3px;
                  background: #a45c00;
                  border-radius: 2px;
                "
              />
              Challenged
            </span>
            <span style="display: inline-flex; align-items: center; gap: 6px">
              <span
                style="
                  width: 10px;
                  height: 3px;
                  background: #b3261e;
                  border-radius: 2px;
                "
              />
              Blocked
            </span>
            <span style="display: inline-flex; align-items: center; gap: 6px">
              <span
                style="
                  width: 10px;
                  height: 0;
                  border-top: 1.5px dashed #0070f3;
                "
              />
              Avg score (right axis)
            </span>
          </div>
          <TimelineChart :data="series.data.value" />
        </div>
      </div>
    </section>

    <section
      style="
        display: grid;
        grid-template-columns: 1fr;
        gap: 16px;
        margin-bottom: 16px;
      "
    >
      <div class="card" style="padding: 0">
        <div
          style="
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 16px 20px;
            border-bottom: 1px solid var(--border);
          "
        >
          <div>
            <div style="font-weight: 500">Live evaluations</div>
            <div class="subtle" style="font-size: 0.8125rem">
              Polling every 1.2s — newest first
            </div>
          </div>
          <div
            v-if="eventsData.error.value"
            class="mono"
            style="color: var(--red); font-size: 0.75rem"
          >
            {{ eventsData.error.value }}
          </div>
        </div>
        <EventsTable :events="eventsData.data.value?.events ?? []" />
      </div>
    </section>

    <section
      style="
        display: grid;
        grid-template-columns: 1.2fr 1fr;
        gap: 16px;
      "
    >
      <div class="card" style="padding: 0">
        <div
          style="
            padding: 16px 20px;
            border-bottom: 1px solid var(--border);
          "
        >
          <div style="font-weight: 500">Top flagged fingerprints</div>
          <div class="subtle" style="font-size: 0.8125rem">
            Cross-app reputation — reused across every operator
          </div>
        </div>
        <FingerprintsTable :items="fps.data.value?.items ?? []" />
      </div>

      <div class="card" style="padding: 0">
        <div
          style="
            padding: 16px 20px;
            border-bottom: 1px solid var(--border);
          "
        >
          <div style="font-weight: 500">Operators</div>
          <div class="subtle" style="font-size: 0.8125rem">
            Live pool balances — debited per evaluation
          </div>
        </div>
        <OperatorsTable
          :items="ops.data.value?.items ?? []"
          :eval-cost="ops.data.value?.eval_cost_usdc ?? 0.0001"
        />
      </div>
    </section>
  </div>
</template>
