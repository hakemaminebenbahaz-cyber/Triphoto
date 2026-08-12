import pytest


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
    assert body["label"] in {"carton", "verre", "metal", "papier", "plastique", "poubelle_generale"}
    assert 0 <= body["confidence"] <= 1
    assert body["disposal_hint"]
    assert body["model_version"] == "stub-v0"
    assert len(body["top_predictions"]) == 3
    assert body["top_predictions"][0]["label"] == body["label"]
    assert body["top_predictions"][0]["confidence"] == body["confidence"]
    confidences = [p["confidence"] for p in body["top_predictions"]]
    assert confidences == sorted(confidences, reverse=True)
    assert len({p["label"] for p in body["top_predictions"]}) == 3  # trois matières distinctes


def test_predict_is_deterministic_for_the_same_image(client, auth_headers):
    files = {"file": ("waste.jpg", b"toujours-la-meme-image", "image/jpeg")}
    first = client.post("/predict", headers=auth_headers, files=files)
    second = client.post("/predict", headers=auth_headers, files=files)
    assert first.json()["label"] == second.json()["label"]


def _has_trained_model() -> bool:
    import os

    repo_root = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
    return os.path.exists(os.path.join(repo_root, "ml", "models", "waste_classifier.onnx"))


@pytest.mark.skipif(not _has_trained_model(), reason="ml/models/waste_classifier.onnx absent (non versionné, à entraîner localement)")
def test_predict_uses_real_model_on_a_genuine_image(client, auth_headers):
    """Vérifie le branchement réel API <-> modèle ONNX quand celui-ci est présent
    (télécharger le dataset + lancer ml/scripts/train.py pour le générer)."""
    from io import BytesIO

    from PIL import Image

    buffer = BytesIO()
    Image.new("RGB", (300, 300), color=(200, 200, 210)).save(buffer, format="JPEG")

    response = client.post(
        "/predict",
        headers=auth_headers,
        files={"file": ("waste.jpg", buffer.getvalue(), "image/jpeg")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["model_version"] == "waste_classifier-v1-mobilenetv3"
    assert body["label"] in {"carton", "verre", "metal", "papier", "plastique", "poubelle_generale"}
    assert len(body["top_predictions"]) == 3
    confidences = [p["confidence"] for p in body["top_predictions"]]
    assert confidences == sorted(confidences, reverse=True)
