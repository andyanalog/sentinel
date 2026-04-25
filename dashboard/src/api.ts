export const API_BASE =
  (import.meta.env.VITE_SENTINEL_API as string | undefined) ??
  "http://localhost:8000";

export type Action = "ALLOW" | "CHALLENGE" | "BLOCK";

export interface EvalEvent {
  eval_id: string;
  operator_id: string;
  action: Action;
  score: number;
  fingerprint: string;
  signals: Record<string, number>;
  ts: number;
}

export interface EventsResponse {
  cursor: number;
  counts: Record<Action, number>;
  events: EvalEvent[];
}

export interface FingerprintRow {
  fingerprint: string;
  hits: number;
  max_score: number;
  last_action: Action;
  operators: string[];
}

export interface OperatorRow {
  id: string;
  name: string;
  balance_usdc: number;
}

export interface HealthResponse {
  status: string;
  dummy_mode: boolean;
}

async function get<T>(path: string): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`);
  if (!resp.ok) throw new Error(`${path} → ${resp.status}`);
  return (await resp.json()) as T;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!resp.ok) throw new Error(`${path} → ${resp.status}`);
  return (await resp.json()) as T;
}

export interface TimeseriesResponse {
  bucket_seconds: number;
  window_seconds: number;
  timestamps: number[];            // unix seconds, one per bucket (bucket-aligned)
  partial_fraction: number;        // 0..1, how far into the rightmost bucket
  allow: number[];
  challenge: number[];
  block: number[];
  avg_score: (number | null)[];
}

export const api = {
  health: () => get<HealthResponse>("/health"),
  events: (limit = 100) =>
    get<EventsResponse>(`/v1/dashboard/events?limit=${limit}`),
  fingerprints: (limit = 10) =>
    get<{ items: FingerprintRow[] }>(
      `/v1/dashboard/fingerprints?limit=${limit}`,
    ),
  operators: () =>
    get<{ items: OperatorRow[]; eval_cost_usdc: number }>(
      "/v1/dashboard/operators",
    ),
  timeseries: (windowSeconds: number, bucketSeconds: number) =>
    get<TimeseriesResponse>(
      `/v1/dashboard/timeseries?window=${windowSeconds}&bucket=${bucketSeconds}`,
    ),
  credit: (operatorId: string, amountUsdc: number) =>
    post<{ operator_id: string; balance_usdc: number }>(
      `/v1/operators/${operatorId}/credit`,
      { amount_usdc: amountUsdc },
    ),
};
