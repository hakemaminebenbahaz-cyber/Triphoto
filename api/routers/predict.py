"""Endpoint principal : classification d'une photo de déchet (C9, C10)."""

import time

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from api.core.config import Settings, get_settings
from api.core.metrics import PREDICTION_CONFIDENCE, PREDICTION_ERRORS_TOTAL, PREDICTION_LATENCY_SECONDS, PREDICTIONS_TOTAL
from api.core.model import ModelWrapper, get_model
from api.core.security import get_current_subject
from api.schemas.responses import PredictionResponse

router = APIRouter(prefix="/predict", tags=["predict"])

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE_BYTES = 8 * 1024 * 1024  # 8 Mo

DISPOSAL_HINTS = {
    "verre": "Bac à verre",
    "plastique": "Bac jaune (tri sélectif)",
    "carton": "Bac jaune (tri sélectif)",
    "papier": "Bac jaune (tri sélectif)",
    "metal": "Bac jaune (tri sélectif)",
    "poubelle_generale": "Bac ordures ménagères",
}


@router.post("", response_model=PredictionResponse)
async def predict_waste_category(
    file: UploadFile,
    subject: str = Depends(get_current_subject),
    settings: Settings = Depends(get_settings),
) -> PredictionResponse:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        PREDICTION_ERRORS_TOTAL.labels(reason="unsupported_content_type").inc()
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Format non supporté : {file.content_type}. Utilisez JPEG, PNG ou WebP.",
        )

    image_bytes = await file.read()
    if len(image_bytes) > MAX_FILE_SIZE_BYTES:
        PREDICTION_ERRORS_TOTAL.labels(reason="file_too_large").inc()
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Image trop volumineuse (max 8 Mo).")
    if not image_bytes:
        PREDICTION_ERRORS_TOTAL.labels(reason="empty_file").inc()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fichier vide.")

    model: ModelWrapper = get_model(settings)

    start = time.perf_counter()
    result = model.predict(image_bytes)
    PREDICTION_LATENCY_SECONDS.observe(time.perf_counter() - start)

    PREDICTIONS_TOTAL.labels(label=result["label"], model_mode=result["mode"]).inc()
    PREDICTION_CONFIDENCE.observe(result["confidence"])

    return PredictionResponse(
        label=result["label"],
        confidence=result["confidence"],
        model_version=result["model_version"],
        disposal_hint=DISPOSAL_HINTS.get(result["label"], "Bac ordures ménagères"),
        top_predictions=result["top_predictions"],
    )
