export { SentinelClient } from "./client.js";
export { buildEvalRequest, extractClientIp, normalizeHeaders } from "./fingerprint.js";
export { expressMiddleware } from "./middleware/express.js";
export { fastifyPlugin } from "./middleware/fastify.js";
export { honoMiddleware } from "./middleware/hono.js";
export type {
  Action,
  EvaluationRequest,
  EvaluationResult,
  MiddlewareOptions,
  SentinelClientOptions,
} from "./types.js";

import { SentinelClient } from "./client.js";
import { expressMiddleware } from "./middleware/express.js";
import type { SentinelClientOptions } from "./types.js";

/** Convenience factory matching the README one-liner:
 *     app.use(sentinel({ apiKey }).middleware())
 */
export function sentinel(opts: SentinelClientOptions) {
  const client = new SentinelClient(opts);
  return {
    client,
    middleware: () => expressMiddleware(client),
    evaluate: (overrides?: { costWeight?: number }) =>
      expressMiddleware(client, overrides),
  };
}
