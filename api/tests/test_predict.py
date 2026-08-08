def test_predict_requires_authentication(client):
    response = client.post("/predict", files={"file": ("waste.jpg", b"fake-bytes", "image/jpeg")})
    assert response.status_code in (401, 403)


def test_predict_rejects_unsupported_content_type(client, auth_headers):
    response = client.post(
        "/predict",
        headers=auth_headers,
        files={"file": ("waste.txt", b"not-an-image", "text/plain")},
    )
    assert response.status_code == 415


def test_predict_rejects_empty_file(client, auth_headers):
    response = client.post(
        "/predict",
        headers=auth_headers,
        files={"file": ("waste.jpg", b"", "image/jpeg")},
    )
    assert response.status_code == 400


def test_predict_returns_a_known_label(client, auth_headers):
    response = client.post(
        "/predict",
        headers=auth_headers,
        files={"file": ("waste.jpg", b"une-photo-de-bouteille-en-verre", "image/jpeg")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["label"] in {"verre", "plastique", "carton", "metal", "organique", "poubelle_generale"}
    assert 0 <= body["confidence"] <= 1
    assert body["disposal_hint"]
    assert body["model_version"] == "stub-v0"


def test_predict_is_deterministic_for_the_same_image(client, auth_headers):
    files = {"file": ("waste.jpg", b"toujours-la-meme-image", "image/jpeg")}
    first = client.post("/predict", headers=auth_headers, files=files)
    second = client.post("/predict", headers=auth_headers, files=files)
    assert first.json()["label"] == second.json()["label"]
