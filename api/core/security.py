"""Émission et vérification des tokens JWT (accès + rafraîchissement).

Couvre explicitement le critère C10 : "les éventuelles étapes d'authentification
et de renouvellement de l'authentification (expiration des jetons par exemple)
sont intégrées correctement".
"""

from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError, jwt

from api.core.config import Settings, get_settings

bearer_scheme = HTTPBearer(auto_error=True)

TokenType = Literal["access", "refresh"]


def _create_token(subject: str, token_type: TokenType, expires_delta: timedelta, settings: Settings) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str, settings: Settings) -> str:
    return _create_token(
        subject, "access", timedelta(minutes=settings.access_token_expire_minutes), settings
    )


def create_refresh_token(subject: str, settings: Settings) -> str:
    return _create_token(
        subject, "refresh", timedelta(days=settings.refresh_token_expire_days), settings
    )


def decode_token(token: str, settings: Settings, expected_type: TokenType) -> dict:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "token_expired", "message": "Le token a expiré, utilisez /auth/refresh."},
        )
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide.")

    if payload.get("type") != expected_type:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Type de token incorrect.")

    return payload


def get_current_subject(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> str:
    """Dépendance FastAPI : protège un endpoint avec un access token valide."""
    payload = decode_token(credentials.credentials, settings, expected_type="access")
    return payload["sub"]
