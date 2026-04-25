export type Action = "ALLOW" | "CHALLENGE" | "BLOCK";

export interface EvaluationRequest {
  ip: string;
  user_agent?: string;
  path?: string;
  method?: string;
  headers?: Record<string, string>;
  timestamp?: string;
}

export interface EvaluationResult {
  action: Action;
  score: number;
  signals: Record<string, number>;
  fingerprint: string;
  eval_id: string;
}

export interface SentinelClientOptions {
  apiKey: string;
  endpoint?: string;            // default: http://localhost:8000
  timeoutMs?: number;           // default: 1500
  failOpen?: boolean;           // on network error, default true
}

export interface MiddlewareOptions {
  costWeight?: number;          // future: per-route weighted cost
  onDecision?: (r: EvaluationResult) => void;
}
