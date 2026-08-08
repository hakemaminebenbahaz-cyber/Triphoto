"""Émission et renouvellement des tokens d'accès à l'API (C9, C10).

Endpoint de démo : un seul couple client_id/client_secret défini en config.
À remplacer par une vraie gestion d'utilisateurs si le projet grandit.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from api.core.config import Settings, get_settings
from api.core.security import create_access_token, create_refresh_token, decode_token
from api.schemas.requests import RefreshRequest, TokenRequest
from api.schemas.responses import TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=TokenResponse)
def login(payload: TokenRequest, settings: Settings = Depends(get_settings)) -> TokenResponse:
    if payload.client_id != settings.demo_client_id or payload.client_secret != settings.demo_client_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants invalides.")

    return TokenResponse(
        access_token=create_access_token(payload.client_id, settings),
        refresh_token=create_refresh_token(payload.client_id, settings),
        expires_in_minutes=settings.access_token_expire_minutes,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, settings: Settings = Depends(get_settings)) -> TokenResponse:
    """Échange un refresh token valide contre un nouveau couple de tokens.

    C'est ce endpoint qui couvre le critère C10 sur le "renouvellement de
    l'authentification (expiration des jetons)" : le client appelle /auth/refresh
    dès que /predict répond 401 {"error": "token_expired"}.
    """
    token_payload = decode_token(payload.refresh_token, settings, expected_type="refresh")
    subject = token_payload["sub"]

    return TokenResponse(
        access_token=create_access_token(subject, settings),
        refresh_token=create_refresh_token(subject, settings),
        expires_in_minutes=settings.access_token_expire_minutes,
    )
