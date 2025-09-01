from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.config import settings

description = """
Tray MCP Server - A FastAPI-based Model Context Protocol server for integrating with Tray e-commerce platform.

This server provides:

* OAuth2 authentication with Tray
* Webhook handling for real-time notifications
* API client for Tray's REST endpoints
* Secure token management
"""

app = FastAPI(
    title="Tray MCP Server",
    description=description,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Tray MCP Server is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
