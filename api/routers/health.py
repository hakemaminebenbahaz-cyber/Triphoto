"""Endpoint public de santé — utilisé par le monitorage applicatif (C11, C20)."""

from fastapi import APIRouter, Depends

from api.core.config import Settings, get_settings
from api.core.model import get_model
from api.schemas.responses import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    model = get_model(settings)
    return HealthResponse(status="ok", model_mode=model.mode, api_version=settings.api_version)
