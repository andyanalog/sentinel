import { afterEach, describe, expect, it, vi } from "vitest";

import { SentinelClient } from "../src/client.js";

describe("SentinelClient", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("posts to /v1/evaluate with bearer auth", async () => {
    const fetchMock = vi.fn(async () =>
      new Response(
        JSON.stringify({
          action: "ALLOW",
          score: 10,
          signals: {},
          fingerprint: "0xabc",
          eval_id: "ev_1",
        }),
        { status: 200 },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    const client = new SentinelClient({ apiKey: "sk_test", endpoint: "http://x" });
    const result = await client.evaluate({ ip: "1.2.3.4" });

    expect(result.action).toBe("ALLOW");
    expect(fetchMock).toHaveBeenCalledWith(
      "http://x/v1/evaluate",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({ Authorization: "Bearer sk_test" }),
      }),
    );
  });

  it("fails open on network error by default", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => { throw new Error("boom"); }));
    const client = new SentinelClient({ apiKey: "sk_test" });
    const result = await client.evaluate({ ip: "1.2.3.4" });
    expect(result.action).toBe("ALLOW");
    expect(result.signals.fail_open).toBe(1);
  });

  it("throws when failOpen is disabled", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => { throw new Error("boom"); }));
    const client = new SentinelClient({ apiKey: "sk_test", failOpen: false });
    await expect(client.evaluate({ ip: "1.2.3.4" })).rejects.toThrow();
  });
});
