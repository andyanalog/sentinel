import { SentinelClient } from "../client.js";
import { buildEvalRequest } from "../fingerprint.js";
import type {
  MiddlewareOptions,
  SentinelClientOptions,
} from "../types.js";

type HonoContext = {
  req: {
    header(name: string): string | undefined;
    path: string;
    method: string;
    raw: { headers: Headers };
  };
  json(body: unknown, status?: number): Response;
  set(key: string, value: unknown): void;
};

export function honoMiddleware(
  clientOrOptions: SentinelClient | SentinelClientOptions,
  mwOptions: MiddlewareOptions = {},
) {
  const client =
    clientOrOptions instanceof SentinelClient
      ? clientOrOptions
      : new SentinelClient(clientOrOptions);

  return async function (c: HonoContext, next: () => Promise<void>) {
    const headers: Record<string, string> = {};
    c.req.raw.headers.forEach((v, k) => (headers[k.toLowerCase()] = v));
    const evalReq = buildEvalRequest({
      userAgent: c.req.header("user-agent"),
      path: c.req.path,
      method: c.req.method,
      headers,
    });
    const result = await client.evaluate(evalReq);
    c.set("sentinel", result);
    mwOptions.onDecision?.(result);
    if (result.action === "BLOCK") {
      return c.json(
        { error: "blocked_by_sentinel", score: result.score, eval_id: result.eval_id },
        429,
      );
    }
    await next();
    return;
  };
}
