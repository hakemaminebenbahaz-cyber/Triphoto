from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

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

# Monitorage (C11) : /metrics expose à la fois les métriques HTTP génériques
# (latence, codes retour, en-cours par endpoint — "bonne santé du système")
# et les métriques métier définies dans api/core/metrics.py, enregistrées
# dans le même registre Prometheus global.
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=True)
