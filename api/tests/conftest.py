import pytest
from fastapi.testclient import TestClient

from api.core.config import get_settings
from api.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def auth_headers(client: TestClient) -> dict:
    settings = get_settings()
    response = client.post(
        "/auth/token",
        json={"client_id": settings.demo_client_id, "client_secret": settings.demo_client_secret},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
