from pydantic import BaseModel, ConfigDict


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


class HealthResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    status: str
    model_mode: str
    api_version: str


class LabelScore(BaseModel):
    label: str
    confidence: float


class PredictionResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    label: str
    confidence: float
    model_version: str
    disposal_hint: str
    top_predictions: list[LabelScore]


class ErrorResponse(BaseModel):
    error: str
    message: str
