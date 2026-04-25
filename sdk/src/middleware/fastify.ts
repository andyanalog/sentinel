import { SentinelClient } from "../client.js";
import { buildEvalRequest } from "../fingerprint.js";
import type {
  EvaluationResult,
  MiddlewareOptions,
  SentinelClientOptions,
} from "../types.js";

// Minimal structural types — avoids a hard dep on fastify.
type FastifyReq = {
  ip?: string;
  headers: Record<string, string | string[] | undefined>;
  url: string;
  method: string;
  sentinel?: EvaluationResult;
};
type FastifyReply = {
  code(status: number): FastifyReply;
  send(body: unknown): unknown;
};
type FastifyInstance = {
  addHook(name: "preHandler", handler: (req: FastifyReq, reply: FastifyReply) => Promise<void>): void;
};

export function fastifyPlugin(
  clientOrOptions: SentinelClient | SentinelClientOptions,
  mwOptions: MiddlewareOptions = {},
) {
  const client =
    clientOrOptions instanceof SentinelClient
      ? clientOrOptions
      : new SentinelClient(clientOrOptions);

  return async function register(app: FastifyInstance) {
    app.addHook("preHandler", async (req, reply) => {
      const evalReq = buildEvalRequest({
        ip: req.ip,
        userAgent: (req.headers["user-agent"] as string) ?? undefined,
        path: req.url,
        method: req.method,
        headers: req.headers,
      });
      const result = await client.evaluate(evalReq);
      req.sentinel = result;
      mwOptions.onDecision?.(result);
      if (result.action === "BLOCK") {
        reply.code(429).send({
          error: "blocked_by_sentinel",
          score: result.score,
          eval_id: result.eval_id,
        });
      }
    });
  };
}
