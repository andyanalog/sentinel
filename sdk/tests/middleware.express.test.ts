import express from "express";
import request from "supertest";
import { afterEach, describe, expect, it, vi } from "vitest";

import { expressMiddleware } from "../src/middleware/express.js";

function mockEvaluate(result: { action: string; score: number }) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () =>
      new Response(
        JSON.stringify({
          ...result,
          signals: {},
          fingerprint: "0xabc",
          eval_id: "ev_1",
        }),
        { status: 200 },
      ),
    ),
  );
}

describe("expressMiddleware", () => {
  afterEach(() => vi.restoreAllMocks());

  it("allows requests when action=ALLOW", async () => {
    mockEvaluate({ action: "ALLOW", score: 5 });
    const app = express();
    app.use(expressMiddleware({ apiKey: "sk_test" }));
    app.get("/", (_req, res) => res.send("ok"));

    const resp = await request(app).get("/");
    expect(resp.status).toBe(200);
    expect(resp.text).toBe("ok");
  });

  it("returns 429 when action=BLOCK", async () => {
    mockEvaluate({ action: "BLOCK", score: 90 });
    const app = express();
    app.use(expressMiddleware({ apiKey: "sk_test" }));
    app.get("/", (_req, res) => res.send("should not reach"));

    const resp = await request(app).get("/");
    expect(resp.status).toBe(429);
    expect(resp.body.error).toBe("blocked_by_sentinel");
  });
});
