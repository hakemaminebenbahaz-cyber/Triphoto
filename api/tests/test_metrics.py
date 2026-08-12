"""Tests du monitorage (C11) : /metrics expose bien les métriques métier
attendues, et leurs valeurs évoluent quand l'API est sollicitée.

Les métriques Prometheus vivent dans un registre global du process : on
raisonne donc en delta (avant/après) plutôt qu'en valeur absolue, pour rester
indépendant de l'ordre d'exécution des autres tests du fichier."""

import re


def _metric_value(metrics_text: str, metric_line_prefix: str) -> float:
    """Extrait la valeur d'une ligne de métrique Prometheus, ex:
    _metric_value(text, 'triphoto_predictions_total{label="verre",model_mode="stub"}')
    Retourne 0.0 si la série n'existe pas encore (pas encore observée)."""
    pattern = re.escape(metric_line_prefix) + r"\s+([0-9.eE+-]+)"
    match = re.search(pattern, metrics_text)
    return float(match.group(1)) if match else 0.0


def test_metrics_endpoint_is_exposed_in_prometheus_format(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert "triphoto_predictions_total" in response.text
    assert "triphoto_prediction_confidence" in response.text
    assert "triphoto_prediction_errors_total" in response.text
    assert "triphoto_prediction_latency_seconds" in response.text


def test_successful_prediction_increments_predictions_total(client, auth_headers):
    # bytes non décodables comme image : force le mode stub, que le modèle
    # ONNX soit chargé ou non dans cet environnement (voir model.py fallback).
    files = {"file": ("waste.jpg", b"contenu-non-decodable-comme-image", "image/jpeg")}

    prediction = client.post("/predict", headers=auth_headers, files=files).json()
    assert prediction["model_version"] == "stub-v0"

    series = f'triphoto_predictions_total{{label="{prediction["label"]}",model_mode="stub"}}'
    before = _metric_value(client.get("/metrics").text, series)
    client.post("/predict", headers=auth_headers, files=files)
    after = _metric_value(client.get("/metrics").text, series)

    assert after == before + 1


def test_unsupported_content_type_increments_error_counter(client, auth_headers):
    series = 'triphoto_prediction_errors_total{reason="unsupported_content_type"}'
    before = _metric_value(client.get("/metrics").text, series)

    client.post(
        "/predict",
        headers=auth_headers,
        files={"file": ("waste.txt", b"not-an-image", "text/plain")},
    )

    after = _metric_value(client.get("/metrics").text, series)
    assert after == before + 1


def test_prediction_confidence_histogram_observes_values(client, auth_headers):
    before_count = _metric_value(client.get("/metrics").text, "triphoto_prediction_confidence_count")

    client.post(
        "/predict",
        headers=auth_headers,
        files={"file": ("waste.jpg", b"une-autre-image-quelconque", "image/jpeg")},
    )

    after_count = _metric_value(client.get("/metrics").text, "triphoto_prediction_confidence_count")
    assert after_count == before_count + 1
