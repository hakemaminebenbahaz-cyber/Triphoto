def test_health_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["model_mode"] in {"stub", "onnx"}
    assert body["api_version"] == "0.1.0"
