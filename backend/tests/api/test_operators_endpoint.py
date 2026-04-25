async def test_create_operator_returns_key_and_pool(client):
    resp = await client.post("/v1/operators", json={"name": "demo-app"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["operator"]["api_key"].startswith("sk_")
    assert body["pool"]["balance_usdc"] == 100.0  # dummy seed


async def test_credit_pool(client):
    created = await client.post("/v1/operators", json={"name": "x"})
    op_id = created.json()["operator"]["id"]
    resp = await client.post(
        f"/v1/operators/{op_id}/credit", json={"amount_usdc": 50.0}
    )
    assert resp.status_code == 200
    assert resp.json()["balance_usdc"] == 150.0


async def test_health_reports_dummy_mode(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "dummy_mode": True}
