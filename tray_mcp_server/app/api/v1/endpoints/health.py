from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.auth.oauth2 import get_current_user

router = APIRouter()

@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Tray MCP Server",
        "version": "1.0.0"
    }

@router.get("/health/auth", response_model=Dict[str, Any])
async def auth_health_check(current_user: dict = Depends(get_current_user)):
    """Health check endpoint that requires authentication"""
    return {
        "status": "healthy",
        "service": "Tray MCP Server",
        "authenticated": True,
        "user": current_user.get("sub") if current_user else None
    }
