from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.core.config import get_settings
from api.routers import auth, health, predict

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.api_version,
    description="API de classification de déchets par photo — projet TriPhoto (RNCP37827, E3).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(predict.router)
