<script setup lang="ts">
import {
  Chart,
  CategoryScale,
  Filler,
  LinearScale,
  LineController,
  LineElement,
  PointElement,
  Tooltip,
} from "chart.js";
import { onBeforeUnmount, onMounted, ref, watch } from "vue";

import type { TimeseriesResponse } from "../api";

Chart.register(
  CategoryScale,
  LinearScale,
  LineController,
  LineElement,
  PointElement,
  Filler,
  Tooltip,
);

const props = defineProps<{
  data: TimeseriesResponse | null;
}>();

const canvas = ref<HTMLCanvasElement | null>(null);
let chart: Chart | null = null;

// Chart.js plugin: draws a thin vertical guide at the hovered bucket, plus
// a soft band over the in-progress bucket so viewers know the rightmost
// count is still accumulating.
const crosshairAndPartialPlugin = {
  id: "crosshairAndPartial",
  afterDatasetsDraw(c: Chart) {
    const { ctx, chartArea, scales } = c;
    if (!chartArea) return;

    const partialIdx: number | undefined = (c.options as any).__partialIndex;
    if (partialIdx !== undefined && partialIdx >= 0) {
      const x0 = scales.x.getPixelForValue(partialIdx - 0.5);
      const x1 = scales.x.getPixelForValue(partialIdx + 0.5);
      ctx.save();
      ctx.fillStyle = "rgba(0, 0, 0, 0.035)";
      ctx.fillRect(x0, chartArea.top, x1 - x0, chartArea.bottom - chartArea.top);
      ctx.restore();
    }

    const active = c.tooltip?.getActiveElements?.();
    if (active && active.length) {
      const x = active[0].element.x;
      ctx.save();
      ctx.beginPath();
      ctx.moveTo(x, chartArea.top);
      ctx.lineTo(x, chartArea.bottom);
      ctx.lineWidth = 1;
      ctx.strokeStyle = "#d4d4d4";
      ctx.setLineDash([3, 3]);
      ctx.stroke();
      ctx.restore();
    }
  },
};

function fmtTime(ts: number, bucket: number): string {
  const d = new Date(ts * 1000);
  // Minute precision for coarse buckets (≥ 60s), second precision otherwise.
  return bucket >= 60
    ? d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" })
    : d.toLocaleTimeString(undefined, {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
}

function render() {
  if (!canvas.value || !props.data) return;
  const d = props.data;
  const labels = d.timestamps.map((t) => fmtTime(t, d.bucket_seconds));
  const partialIdx = d.timestamps.length - 1;

  if (!chart) {
    chart = new Chart(canvas.value, {
      type: "line",
      plugins: [crosshairAndPartialPlugin],
      data: {
        labels,
        datasets: [
          {
            label: "Allowed",
            data: d.allow,
            borderColor: "#0a7d3a",
            backgroundColor: "rgba(10, 125, 58, 0.12)",
            fill: true,
            tension: 0.28,
            pointRadius: 0,
            pointHoverRadius: 3,
            borderWidth: 1.5,
            yAxisID: "y",
          },
          {
            label: "Challenged",
            data: d.challenge,
            borderColor: "#a45c00",
            backgroundColor: "rgba(164, 92, 0, 0.12)",
            fill: true,
            tension: 0.28,
            pointRadius: 0,
            pointHoverRadius: 3,
            borderWidth: 1.5,
            yAxisID: "y",
          },
          {
            label: "Blocked",
            data: d.block,
            borderColor: "#b3261e",
            backgroundColor: "rgba(179, 38, 30, 0.14)",
            fill: true,
            tension: 0.28,
            pointRadius: 0,
            pointHoverRadius: 3,
            borderWidth: 1.5,
            yAxisID: "y",
          },
          {
            label: "Avg score",
            data: d.avg_score as number[],
            borderColor: "#0070f3",
            backgroundColor: "transparent",
            borderDash: [4, 4],
            borderWidth: 1.25,
            pointRadius: 0,
            pointHoverRadius: 3,
            fill: false,
            tension: 0.24,
            spanGaps: true,
            yAxisID: "y1",
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        // Animations off entirely — the poll cadence is the animation.
        // This is the single biggest fix for the "moving every second"
        // feeling: once bucket edges are snapped and updates are
        // instantaneous, the chart stops visibly sliding.
        animation: false,
        animations: { colors: false, x: false, y: false },
        transitions: { active: { animation: { duration: 0 } } },
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: "#0a0a0a",
            borderColor: "#0a0a0a",
            padding: 10,
            titleFont: { weight: "500", size: 12 },
            bodyFont: { size: 12 },
            callbacks: {
              title: (items) => {
                const label = items[0]?.label ?? "";
                const idx = items[0]?.dataIndex;
                if (idx === partialIdx) return `${label}  ·  in progress`;
                return label;
              },
              label: (ctx) => {
                const v = ctx.parsed.y;
                if (v === null || v === undefined) return "";
                return ` ${ctx.dataset.label}: ${v}`;
              },
            },
          },
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: {
              color: "#8f8f8f",
              autoSkip: true,
              maxTicksLimit: 8,
              font: { size: 11 },
              // Don't show a label under the in-progress bucket — its
              // position is stable but naming it exactly can mislead.
            },
            border: { color: "#eaeaea" },
          },
          y: {
            title: {
              display: true,
              text: "Requests / bucket",
              color: "#8f8f8f",
              font: { size: 11, weight: "500" },
            },
            beginAtZero: true,
            grid: { color: "#f1f1f1" },
            ticks: {
              color: "#8f8f8f",
              precision: 0,
              font: { size: 11 },
            },
            border: { display: false },
          },
          y1: {
            position: "right",
            title: {
              display: true,
              text: "Avg score",
              color: "#0070f3",
              font: { size: 11, weight: "500" },
            },
            min: 0,
            max: 100,
            grid: { display: false },
            ticks: {
              color: "#0070f3",
              font: { size: 11 },
              callback: (v) => `${v}`,
            },
            border: { display: false },
          },
        },
      },
    });
    (chart.options as any).__partialIndex = partialIdx;
  } else {
    chart.data.labels = labels;
    chart.data.datasets[0].data = d.allow;
    chart.data.datasets[1].data = d.challenge;
    chart.data.datasets[2].data = d.block;
    chart.data.datasets[3].data = d.avg_score as number[];
    (chart.options as any).__partialIndex = partialIdx;
    chart.update("none");   // "none" = skip animation on update
  }
}

onMounted(render);
watch(() => props.data, render, { deep: true });
onBeforeUnmount(() => {
  chart?.destroy();
  chart = null;
});
</script>

<template>
  <div style="position: relative; width: 100%; height: 280px">
    <canvas ref="canvas" />
  </div>
</template>
