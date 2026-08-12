"""Chargement et exécution du modèle de classification de déchets.

Tant que `ml/scripts/train.py` n'a pas produit et exporté un modèle entraîné
(voir ml/README.md), l'API tourne en mode "stub" : elle renvoie une prédiction
déterministe (basée sur le contenu du fichier) pour que l'API, ses tests et
l'application front soient développables et démontrables indépendamment du
calendrier d'entraînement du modèle.

Dès que ml/models/waste_classifier.onnx existe, il est chargé automatiquement
au démarrage et remplace le mode stub. Le pré-traitement (resize 256 / center
crop 224 / normalisation ImageNet) reproduit exactement les transforms utilisés
à l'entraînement (torchvision MobileNet_V3_Small_Weights.DEFAULT.transforms()),
pour éviter un écart silencieux entre entraînement et inférence.
"""

from __future__ import annotations

import hashlib
import io
import os

import numpy as np
from PIL import Image

from api.core.config import Settings

IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)
RESIZE_SHORT_SIDE = 256
CROP_SIZE = 224


def _resize_shorter_side(image: Image.Image, size: int) -> Image.Image:
    w, h = image.size
    if w <= h:
        new_w, new_h = size, round(h * size / w)
    else:
        new_h, new_w = size, round(w * size / h)
    return image.resize((new_w, new_h), Image.BILINEAR)


def _center_crop(image: Image.Image, size: int) -> Image.Image:
    w, h = image.size
    left = (w - size) // 2
    top = (h - size) // 2
    return image.crop((left, top, left + size, top + size))


def preprocess(image_bytes: bytes) -> np.ndarray:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image = _resize_shorter_side(image, RESIZE_SHORT_SIDE)
    image = _center_crop(image, CROP_SIZE)

    array = np.asarray(image).astype(np.float32) / 255.0  # HWC in [0, 1]
    array = (array - IMAGENET_MEAN) / IMAGENET_STD
    array = array.transpose(2, 0, 1)  # CHW
    return np.expand_dims(array, axis=0).astype(np.float32)  # NCHW


def softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - np.max(logits)
    exp = np.exp(shifted)
    return exp / exp.sum()


class ModelWrapper:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.labels = settings.model_labels
        self.session = None
        self.mode = "stub"
        self._try_load_onnx()

    def _try_load_onnx(self) -> None:
        model_file = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", self.settings.model_path)
        )
        if not os.path.exists(model_file):
            return
        try:
            import onnxruntime as ort  # import tardif : dépendance optionnelle tant que non entraîné

            self.session = ort.InferenceSession(model_file, providers=["CPUExecutionProvider"])
            self.mode = "onnx"
        except ImportError:
            # onnxruntime pas installé : on reste en mode stub sans planter l'API
            self.mode = "stub"

    def predict(self, image_bytes: bytes) -> dict:
        if self.mode == "onnx" and self.session is not None:
            try:
                return self._predict_onnx(image_bytes)
            except Exception:
                # une image illisible ou un modèle corrompu ne doit pas faire planter l'API :
                # on retombe sur le stub plutôt que de renvoyer une 500 opaque au client.
                return self._predict_stub(image_bytes)
        return self._predict_stub(image_bytes)

    def _predict_stub(self, image_bytes: bytes) -> dict:
        digest = hashlib.sha256(image_bytes).hexdigest()
        index = int(digest, 16) % len(self.labels)
        # confiance stable et plausible, dérivée du hash (pas aléatoire à chaque appel)
        confidence = round(min(0.55 + (int(digest[:4], 16) % 40) / 100, 0.99), 4)

        # top-3 synthétique déterministe, décroissant, pour rester cohérent avec
        # le mode onnx côté API/front (voir _predict_onnx) sans prétendre à une
        # vraie distribution de probabilités.
        others = [i for i in range(len(self.labels)) if i != index]
        second = others[int(digest[4:8], 16) % len(others)]
        remaining = [i for i in others if i != second]
        third = remaining[int(digest[8:12], 16) % len(remaining)]

        top_predictions = [
            {"label": self.labels[index], "confidence": confidence},
            {"label": self.labels[second], "confidence": round(confidence * 0.6, 4)},
            {"label": self.labels[third], "confidence": round(confidence * 0.3, 4)},
        ]

        return {
            "label": self.labels[index],
            "confidence": confidence,
            "model_version": "stub-v0",
            # mode réellement utilisé pour CETTE prédiction — peut différer de
            # self.mode quand une image illisible fait retomber le mode "onnx"
            # sur le stub (voir predict()) ; le monitorage (C11) doit refléter
            # ce qui s'est vraiment passé, pas la config statique du wrapper.
            "mode": "stub",
            "top_predictions": top_predictions,
        }

    def _predict_onnx(self, image_bytes: bytes) -> dict:
        input_array = preprocess(image_bytes)
        input_name = self.session.get_inputs()[0].name
        (logits,) = self.session.run(None, {input_name: input_array})

        probabilities = softmax(logits[0])
        ranked = np.argsort(probabilities)[::-1][:3]

        top_predictions = [
            {"label": self.labels[int(i)], "confidence": round(float(probabilities[i]), 4)} for i in ranked
        ]

        return {
            "label": top_predictions[0]["label"],
            "confidence": top_predictions[0]["confidence"],
            "model_version": "waste_classifier-v1-mobilenetv3",
            "mode": "onnx",
            "top_predictions": top_predictions,
        }


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
