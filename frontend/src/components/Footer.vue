<script setup>
import { useRouter } from 'vue-router';
const router = useRouter();
const allCols = {
  Product: [['Home', '/'], ['Services', '/services'], ['Case Studies', '/cases'], ['Contact', '/contact']],
  Developers: [['API Reference', '/services'], ['SDK Docs', '/services'], ['Changelog', '/'], ['Status', '/']],
  Company: [['About', '/'], ['Blog', '/cases'], ['Careers', '/contact'], ['Contact', '/contact']],
  Legal: [['Privacy', '/'], ['Terms', '/'], ['Security', '/']],
};
const hiddenSections = ['Developers', 'Company', 'Legal'];
const cols = Object.fromEntries(
  Object.entries(allCols).filter(([section]) => !hiddenSections.includes(section))
);
</script>

<template>
  <footer class="footer">
    <div class="container">
      <div class="grid">
        <div class="brand">
          <div class="name">Sentinel</div>
          <p class="tag">Trust-as-a-Service. One API call. Allow, challenge, or block.</p>
          <div class="chips">
            <span class="chip">Arc L1</span>
            <span class="chip">USDC</span>
            <span class="chip">x402</span>
          </div>
        </div>
        <div v-for="(items, section) in cols" :key="section" class="col">
          <div class="section">{{ section }}</div>
          <button v-for="[label, to] in items" :key="label" class="flink" @click="router.push(to)">
            {{ label }}
          </button>
        </div>
      </div>
      <div class="bottom">
        <div>© 2026 Sentinel. All rights reserved.</div>
        
      </div>
    </div>
  </footer>
</template>

<style scoped>
.footer { background: #f5f5f5; border-top: var(--border); padding: 64px 0 40px; }
.grid {
  display: grid; grid-template-columns: 2fr 1fr;
  gap: 32px; margin-bottom: 56px;
}
.brand { display: flex; flex-direction: column; gap: 16px; }
.name { font-family: var(--font-display); font-size: 20px; color: #000; letter-spacing: -0.2px; }
.tag { font-size: 14px; line-height: 1.65; color: var(--color-fg-muted); max-width: 240px; letter-spacing: 0.1px; }
.chips { display: flex; gap: 8px; margin-top: 4px; }
.chip {
  font-size: 11px; font-weight: 600; color: var(--color-fg-muted);
  background: rgba(0, 0, 0, 0.06); padding: 4px 10px; border-radius: 9999px;
  letter-spacing: 0.5px; text-transform: uppercase;
}
.col { display: flex; flex-direction: column; gap: 12px; justify-self: end; }
.section { font-size: 11px; font-weight: 700; color: #000; letter-spacing: 0.6px; text-transform: uppercase; }
.flink {
  font-size: 14px; color: var(--color-fg-secondary); background: none; border: none; padding: 0;
  text-align: left; letter-spacing: 0.1px; transition: color 150ms ease; width: fit-content;
}
.flink:hover { color: #000; }
.bottom {
  border-top: var(--border); padding-top: 24px;
  display: flex; justify-content: center; align-items: center;
  font-size: 13px; color: var(--color-fg-muted); letter-spacing: 0.1px;
}
.footer { padding: 64px 0 40px; }
@media (max-width: 900px) {
  .grid { grid-template-columns: 1fr; gap: 32px; margin-bottom: 40px; }
  .brand { grid-column: 1 / -1; }
  .col { justify-self: start; }
}
@media (max-width: 420px) {
  .footer { padding: 48px 0 32px; }
  .bottom { flex-direction: column; gap: 8px; align-items: center; }
}
</style>
