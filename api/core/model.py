"""Chargement et exécution du modèle de classification de déchets.

Tant que `ml/scripts/train.py` n'a pas produit et exporté un modèle entraîné
(voir ml/README.md), l'API tourne en mode "stub" : elle renvoie une prédiction
déterministe (basée sur le contenu du fichier) pour que l'API, ses tests et
l'application front soient développables et démontrables indépendamment du
calendrier d'entraînement du modèle.

Une fois le modèle exporté en ONNX (ml/models/waste_classifier.onnx), il est
chargé automatiquement au démarrage et remplace le mode stub.
"""

from __future__ import annotations

import hashlib
import os

from api.core.config import Settings


class ModelWrapper:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.labels = settings.model_labels
        self.session = None
        self.mode = "stub"
        self._try_load_onnx()

    def _try_load_onnx(self) -> None:
        model_file = os.path.join(os.path.dirname(__file__), "..", self.settings.model_path)
        if not os.path.exists(model_file):
            return
        try:
            import onnxruntime as ort  # import tardif : dépendance optionnelle tant que non entraîné

            self.session = ort.InferenceSession(model_file)
            self.mode = "onnx"
        except ImportError:
            # onnxruntime pas installé : on reste en mode stub sans planter l'API
            self.mode = "stub"

    def predict(self, image_bytes: bytes) -> dict:
        if self.mode == "onnx" and self.session is not None:
            return self._predict_onnx(image_bytes)
        return self._predict_stub(image_bytes)

    def _predict_stub(self, image_bytes: bytes) -> dict:
        digest = hashlib.sha256(image_bytes).hexdigest()
        index = int(digest, 16) % len(self.labels)
        # confiance stable et plausible, dérivée du hash (pas aléatoire à chaque appel)
        confidence = 0.55 + (int(digest[:4], 16) % 40) / 100
        return {
            "label": self.labels[index],
            "confidence": round(min(confidence, 0.99), 4),
            "model_version": "stub-v0",
        }

    def _predict_onnx(self, image_bytes: bytes) -> dict:
        raise NotImplementedError(
            "Pré-traitement + inférence ONNX à implémenter une fois le modèle entraîné "
            "(voir ml/scripts/train.py et ml/scripts/evaluate.py)."
        )


_model_singleton: ModelWrapper | None = None


def get_model(settings: Settings) -> ModelWrapper:
    """Retourne une instance unique du modèle (chargé une seule fois au premier appel).

    Pas de lru_cache ici : Settings (pydantic) n'est pas garanti hashable, on gère
    donc le singleton nous-mêmes plutôt que de dépendre du hash de l'argument.
    """
    global _model_singleton
    if _model_singleton is None:
        _model_singleton = ModelWrapper(settings)
    return _model_singleton
