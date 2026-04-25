import type {
  EvaluationRequest,
  EvaluationResult,
  SentinelClientOptions,
} from "./types.js";

const DEFAULT_ENDPOINT = "http://localhost:8000";
const DEFAULT_TIMEOUT = 1500;

export class SentinelClient {
  private readonly apiKey: string;
  private readonly endpoint: string;
  private readonly timeoutMs: number;
  private readonly failOpen: boolean;

  constructor(opts: SentinelClientOptions) {
    if (!opts.apiKey) throw new Error("SentinelClient: apiKey is required");
    this.apiKey = opts.apiKey;
    this.endpoint = (opts.endpoint ?? DEFAULT_ENDPOINT).replace(/\/$/, "");
    this.timeoutMs = opts.timeoutMs ?? DEFAULT_TIMEOUT;
    this.failOpen = opts.failOpen ?? true;
  }

  async evaluate(req: EvaluationRequest): Promise<EvaluationResult> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);
    try {
      const resp = await fetch(`${this.endpoint}/v1/evaluate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${this.apiKey}`,
        },
        body: JSON.stringify(req),
        signal: controller.signal,
      });
      if (!resp.ok) {
        if (this.failOpen) return this.allowFallback(req);
        throw new Error(`sentinel evaluate failed: ${resp.status}`);
      }
      return (await resp.json()) as EvaluationResult;
    } catch (err) {
      if (this.failOpen) return this.allowFallback(req);
      throw err;
    } finally {
      clearTimeout(timer);
    }
  }

  private allowFallback(_req: EvaluationRequest): EvaluationResult {
    return {
      action: "ALLOW",
      score: 0,
      signals: { fail_open: 1 },
      fingerprint: "0xfailopen",
      eval_id: `ev_failopen_${Date.now()}`,
    };
  }
}
