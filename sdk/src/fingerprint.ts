import type { EvaluationRequest } from "./types.js";

export function normalizeHeaders(
  headers: Record<string, string | string[] | undefined>,
): Record<string, string> {
  const out: Record<string, string> = {};
  for (const [k, v] of Object.entries(headers)) {
    if (v === undefined) continue;
    out[k.toLowerCase()] = Array.isArray(v) ? v.join(",") : String(v);
  }
  return out;
}

export function extractClientIp(
  headers: Record<string, string>,
  fallback: string | undefined,
): string {
  const xff = headers["x-forwarded-for"];
  if (xff) return xff.split(",")[0]!.trim();
  return headers["x-real-ip"] ?? fallback ?? "0.0.0.0";
}

export function buildEvalRequest(raw: {
  ip?: string;
  userAgent?: string;
  path?: string;
  method?: string;
  headers?: Record<string, string | string[] | undefined>;
}): EvaluationRequest {
  const headers = normalizeHeaders(raw.headers ?? {});
  return {
    ip: raw.ip ?? extractClientIp(headers, raw.ip),
    user_agent: raw.userAgent ?? headers["user-agent"] ?? "",
    path: raw.path ?? "/",
    method: raw.method ?? "GET",
    headers,
    timestamp: new Date().toISOString(),
  };
}
