async def test_evaluate_allow_for_benign_request(client):
    headers = {"Authorization": "Bearer test-key"}
    resp = await client.post(
        "/v1/evaluate",
        headers=headers,
        json={
            "ip": "127.0.0.1",
            "user_agent": "Mozilla/5.0",
            "path": "/",
            "method": "GET",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["action"] in ("ALLOW", "CHALLENGE")
    assert body["fingerprint"].startswith("0x")
    assert body["eval_id"].startswith("ev_")


async def test_evaluate_blocks_on_burst(client):
    headers = {"Authorization": "Bearer burst-key"}
    payload = {
        "ip": "185.220.1.1",  # suspicious range
        "user_agent": "bot/1.0",
        "path": "/api/submit",
        "method": "POST",
    }
    last = None
    for _ in range(30):
        last = await client.post("/v1/evaluate", headers=headers, json=payload)
    assert last is not None
    assert last.status_code == 200
    assert last.json()["action"] == "BLOCK"


async def test_local_ip_burst_is_challenge_not_block(client):
    """By design: traffic from a loopback IP can only reach CHALLENGE via
    burst + reputation alone — benign dev traffic would otherwise be BLOCKed.
    A real BLOCK requires the `ip_asn` signal to fire, which means the demo
    must have `trust proxy` enabled so the bot's spoofed XFF reaches the
    backend. If this assertion flips to BLOCK, lower the thresholds
    deliberately — don't let it happen by accident."""
    headers = {"Authorization": "Bearer local-bot"}
    payload = {
        "ip": "127.0.0.1",
        "user_agent": "BurstBot/1.0",
        "path": "/api/submit",
        "method": "POST",
    }
    last = None
    for _ in range(50):
        last = await client.post("/v1/evaluate", headers=headers, json=payload)
    assert last is not None
    assert last.json()["action"] == "CHALLENGE"


async def test_missing_auth_is_401(client):
    resp = await client.post("/v1/evaluate", json={"ip": "1.2.3.4"})
    assert resp.status_code == 401
