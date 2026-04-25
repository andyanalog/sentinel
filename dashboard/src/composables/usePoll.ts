import { onBeforeUnmount, onMounted, ref } from "vue";

export function usePoll<T>(
  fn: () => Promise<T>,
  intervalMs = 1500,
) {
  const data = ref<T | null>(null);
  const error = ref<string | null>(null);
  const loading = ref(true);
  let timer: number | null = null;
  let cancelled = false;

  async function tick() {
    try {
      const v = await fn();
      if (!cancelled) {
        data.value = v as any;
        error.value = null;
      }
    } catch (e: any) {
      if (!cancelled) error.value = e.message ?? String(e);
    } finally {
      if (!cancelled) {
        loading.value = false;
        timer = window.setTimeout(tick, intervalMs);
      }
    }
  }

  onMounted(tick);
  onBeforeUnmount(() => {
    cancelled = true;
    if (timer) window.clearTimeout(timer);
  });

  return { data, error, loading };
}
