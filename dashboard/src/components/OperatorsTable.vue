<script setup lang="ts">
import { ref } from "vue";
import { api, type OperatorRow } from "../api";

const props = defineProps<{ items: OperatorRow[]; evalCost: number }>();
const emit = defineEmits<{ (e: "credited"): void }>();
const busy = ref<string | null>(null);
const error = ref<string | null>(null);

async function onCredit(op: OperatorRow) {
  const input = prompt(`Credit ${op.name} — amount in USDC?`, "0.01");
  if (!input) return;
  const amount = Number(input);
  if (!Number.isFinite(amount) || amount <= 0) {
    error.value = "enter a positive number";
    return;
  }
  busy.value = op.id;
  error.value = null;
  try {
    await api.credit(op.id, amount);
    emit("credited");
  } catch (e) {
    error.value = (e as Error).message;
  } finally {
    busy.value = null;
  }
}
</script>

<template>
  <table class="plain">
    <thead>
      <tr>
        <th>Operator</th>
        <th>ID</th>
        <th style="width: 160px; text-align: right">Balance (USDC)</th>
        <th style="width: 160px; text-align: right">Evals remaining</th>
        <th style="width: 120px; text-align: right">Actions</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="op in items" :key="op.id">
        <td>{{ op.name }}</td>
        <td class="mono subtle">{{ op.id }}</td>
        <td class="mono" style="text-align: right">
          {{ op.balance_usdc.toFixed(4) }}
        </td>
        <td class="mono subtle" style="text-align: right">
          {{ props.evalCost > 0 ? Math.floor(op.balance_usdc / props.evalCost).toLocaleString() : "∞" }}
        </td>
        <td style="text-align: right">
          <button
            :disabled="busy === op.id"
            @click="onCredit(op)"
            class="credit-btn"
          >
            {{ busy === op.id ? "..." : "Credit" }}
          </button>
        </td>
      </tr>
      <tr v-if="!items.length">
        <td colspan="5" class="subtle" style="text-align: center; padding: 24px">
          No operators registered yet
        </td>
      </tr>
    </tbody>
  </table>
  <div v-if="error" class="error">{{ error }}</div>
</template>

<style scoped>
.credit-btn {
  padding: 4px 10px;
  font-size: 12px;
  cursor: pointer;
}
.credit-btn:disabled {
  opacity: 0.5;
  cursor: wait;
}
.error {
  color: #c00;
  font-size: 12px;
  margin-top: 6px;
}
</style>
