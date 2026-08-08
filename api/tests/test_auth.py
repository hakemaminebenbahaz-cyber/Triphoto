from api.core.config import get_settings
from api.core.security import create_access_token


def test_login_success(client):
    settings = get_settings()
    response = client.post(
        "/auth/token",
        json={"client_id": settings.demo_client_id, "client_secret": settings.demo_client_secret},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


def test_login_wrong_credentials(client):
    response = client.post("/auth/token", json={"client_id": "hacker", "client_secret": "nope"})
    assert response.status_code == 401


def test_refresh_returns_new_access_token(client):
    settings = get_settings()
    login = client.post(
        "/auth/token",
        json={"client_id": settings.demo_client_id, "client_secret": settings.demo_client_secret},
    )
    refresh_token = login.json()["refresh_token"]

    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_refresh_rejects_access_token(client, auth_headers):
    # un access token présenté sur /auth/refresh doit être rejeté (mauvais type de token)
    access_token = auth_headers["Authorization"].split(" ")[1]
    response = client.post("/auth/refresh", json={"refresh_token": access_token})
    assert response.status_code == 401


def test_expired_access_token_is_rejected_with_explicit_error(client, monkeypatch):
    """Couvre le renouvellement de token (C10) : un access token expiré doit
    renvoyer une erreur explicite indiquant au client d'appeler /auth/refresh."""
    settings = get_settings()
    settings.access_token_expire_minutes = -1  # force un token déjà expiré
    expired_token = create_access_token("demo-agent", settings)
    settings.access_token_expire_minutes = 15  # restaure la valeur normale

    response = client.post(
        "/predict",
        headers={"Authorization": f"Bearer {expired_token}"},
        files={"file": ("waste.jpg", b"fake-image-bytes", "image/jpeg")},
    )
    assert response.status_code == 401
    assert response.json()["detail"]["error"] == "token_expired"
