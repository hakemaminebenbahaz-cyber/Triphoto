"""Configuration centralisée de l'API, chargée depuis les variables d'environnement."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", protected_namespaces=()
    )

    # Identité de l'API
    app_name: str = "TriPhoto API"
    api_version: str = "0.1.0"

    # Sécurité / auth (C9, C10)
    secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # Identifiants de démo pour obtenir un token (à remplacer par une vraie gestion utilisateurs)
    demo_client_id: str = "demo-agent"
    demo_client_secret: str = "change-me-too"

    # Modèle (C11, C13)
    model_path: str = "../ml/models/waste_classifier.onnx"
    model_labels: list[str] = [
        "verre",
        "plastique",
        "carton",
        "metal",
        "organique",
        "poubelle_generale",
    ]

    # CORS pour l'app front (C10)
    allowed_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
