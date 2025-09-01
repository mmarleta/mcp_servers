from fastapi import APIRouter
from app.api.v1.endpoints import auth, webhooks, health, tray

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
api_router.include_router(health.router, tags=["health"])
api_router.include_router(tray.router, prefix="/tray", tags=["tray"])
