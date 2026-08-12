"""Métriques du modèle exposées à Prometheus (C11).

Choix des métriques et justification :
- `triphoto_predictions_total{label, model_mode}` : volumétrie par classe prédite.
  Une classe qui se met soudain à dominer anormalement les prédictions est un
  signal classique de dérive des données en entrée (photos hors périmètre
  d'entraînement, changement d'usage, abus).
- `triphoto_prediction_confidence` (histogramme) : distribution de la confiance
  du modèle. Une baisse de la médiane dans le temps est un proxy simple de
  dérive du modèle ou des données, sans avoir besoin des vraies étiquettes
  (jamais disponibles en production ici, puisqu'on ne demande pas à l'usager
  de confirmer la bonne réponse).
- `triphoto_prediction_errors_total{reason}` : erreurs métier (format refusé,
  fichier vide, image illisible) — distinct des erreurs HTTP génériques déjà
  couvertes par prometheus-fastapi-instrumentator (santé du système).
- `triphoto_prediction_latency_seconds` : temps de traitement d'une prédiction
  (hors auth), pour détecter une dégradation de performance du modèle/service.
"""

from prometheus_client import Counter, Histogram

PREDICTIONS_TOTAL = Counter(
    "triphoto_predictions_total",
    "Nombre total de prédictions servies, par label prédit et mode du modèle",
    ["label", "model_mode"],
)

PREDICTION_ERRORS_TOTAL = Counter(
    "triphoto_prediction_errors_total",
    "Nombre d'erreurs métier lors d'une prédiction (hors erreurs HTTP génériques)",
    ["reason"],
)

PREDICTION_CONFIDENCE = Histogram(
    "triphoto_prediction_confidence",
    "Distribution de la confiance du modèle sur les prédictions servies (proxy de dérive)",
    buckets=(0.0, 0.2, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0),
)

PREDICTION_LATENCY_SECONDS = Histogram(
    "triphoto_prediction_latency_seconds",
    "Temps de traitement d'une requête /predict, prétraitement + inférence uniquement",
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)
