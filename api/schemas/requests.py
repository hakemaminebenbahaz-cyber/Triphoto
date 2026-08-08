from pydantic import BaseModel, Field


class TokenRequest(BaseModel):
    client_id: str = Field(..., description="Identifiant du client (agent, application partenaire...)")
    client_secret: str = Field(..., description="Secret associé au client_id")


class RefreshRequest(BaseModel):
    refresh_token: str
