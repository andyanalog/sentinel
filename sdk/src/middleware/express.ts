import type { NextFunction, Request, Response } from "express";

import { SentinelClient } from "../client.js";
import { buildEvalRequest } from "../fingerprint.js";
import type { EvaluationResult, MiddlewareOptions, SentinelClientOptions } from "../types.js";

declare module "express-serve-static-core" {
  interface Request {
    sentinel?: EvaluationResult;
  }
}

export function expressMiddleware(
  clientOrOptions: SentinelClient | SentinelClientOptions,
  mwOptions: MiddlewareOptions = {},
) {
  const client =
    clientOrOptions instanceof SentinelClient
      ? clientOrOptions
      : new SentinelClient(clientOrOptions);

  return async function sentinelMiddleware(
    req: Request,
    res: Response,
    next: NextFunction,
  ) {
    const evalReq = buildEvalRequest({
      ip: req.ip,
      userAgent: req.get("user-agent") ?? undefined,
      path: req.path,
      method: req.method,
      headers: req.headers as Record<string, string | string[] | undefined>,
    });
    const result = await client.evaluate(evalReq);
    req.sentinel = result;
    mwOptions.onDecision?.(result);

    if (result.action === "BLOCK") {
      res.status(429).json({
        error: "blocked_by_sentinel",
        score: result.score,
        eval_id: result.eval_id,
      });
      return;
    }
    next();
  };
}
