from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
import httpx
from app.core.config import settings
from app.auth.oauth2 import create_access_token
from app.services.token_service import TokenService
from datetime import timedelta

router = APIRouter()
token_service = TokenService()

class TrayAuthRequest(BaseModel):
    code: str
    store_host: str
    api_address: str

class TrayAuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "Bearer"

@router.get("/tray/auth-url")
async def get_tray_auth_url(callback_url: str):
    """Generate the Tray authentication URL for OAuth flow"""
    if not settings.TRAY_CONSUMER_KEY:
        raise HTTPException(status_code=500, detail="TRAY_CONSUMER_KEY not configured")
    
    auth_url = f"{settings.TRAY_AUTH_URL}?response_type=code&consumer_key={settings.TRAY_CONSUMER_KEY}&callback={callback_url}"
    return {"auth_url": auth_url}

@router.get("/tray/callback", response_class=HTMLResponse)
async def tray_callback(request: Request, code: str = None, error: str = None):
    """Handle OAuth callback from Tray with detailed debugging"""
    
    # Capture all query parameters for debugging
    all_params = dict(request.query_params)
    
    # Log all parameters for debugging
    print(f"🔍 CALLBACK DEBUG - All parameters received: {all_params}")
    
    if error:
        return f"""
        <html>
            <head><title>Tray Authentication Error</title></head>
            <body>
                <h1>Authentication Error</h1>
                <p>Error: {error}</p>
                <p><strong>All parameters received:</strong></p>
                <pre>{all_params}</pre>
            </body>
        </html>
        """
    
    if code:
        return f"""
        <html>
            <head><title>Tray Authentication Success</title></head>
            <body>
                <h1>✅ Authentication Successful!</h1>
                <p><strong>Authorization code received:</strong> {code}</p>
                <p><strong>All parameters received:</strong></p>
                <pre>{all_params}</pre>
                <p>Now you can exchange this code for an access token using the /api/v1/auth/tray/token endpoint.</p>
                <p><strong>Use this curl command to exchange the code for tokens:</strong></p>
                <pre>
curl -X POST "http://localhost:8002/api/v1/auth/tray/token" -H "accept: application/json" -H "Content-Type: application/json" -d '{{
  "code": "{code}",
  "store_host": "your_store_host",
  "api_address": "https://www.tray.com.br/web_api"
}}'
                </pre>
            </body>
        </html>
        """
    
    # No code received - show debug info
    return f"""
        <html>
            <head><title>Tray Authentication Callback - DEBUG</title></head>
            <body>
                <h1>🔍 Tray Authentication Callback - DEBUG MODE</h1>
                <p><strong>Status:</strong> Waiting for authorization code...</p>
                <p><strong>All parameters received:</strong></p>
                <pre>{all_params}</pre>
                <p><strong>Expected parameters:</strong></p>
                <ul>
                    <li><code>code</code> - Authorization code from Tray</li>
                    <li><code>store</code> - Store ID</li>
                    <li><code>api_address</code> - API address</li>
                    <li><code>store_host</code> - Store host URL</li>
                </ul>
                <p><strong>Debug Info:</strong></p>
                <ul>
                    <li>URL accessed: {request.url}</li>
                    <li>Method: {request.method}</li>
                    <li>Headers: {dict(request.headers)}</li>
                </ul>
            </body>
        </html>
    """

@router.post("/tray/token", response_model=TrayAuthResponse)
async def get_tray_token(auth_request: TrayAuthRequest):
    """Exchange authorization code for access token"""
    if not settings.TRAY_CONSUMER_KEY or not settings.TRAY_CONSUMER_SECRET:
        raise HTTPException(status_code=500, detail="Tray credentials not configured")
    
    # Prepare the token request
    token_url = f"{auth_request.api_address}/auth"
    data = {
        "consumer_key": settings.TRAY_CONSUMER_KEY,
        "consumer_secret": settings.TRAY_CONSUMER_SECRET,
        "code": auth_request.code
    }
    
    # Make the request to Tray API
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(token_url, data=data)
            response.raise_for_status()
            token_data = response.json()
            
            # Store tokens in Redis
            token_service.store_tokens(
                auth_request.store_host,  # Using store_host as seller_id
                {
                    "access_token": token_data["access_token"],
                    "refresh_token": token_data["refresh_token"],
                    "expires_in": token_data.get("expires_in", 3600),
                    "token_type": token_data.get("token_type", "Bearer"),
                    "api_address": auth_request.api_address
                }
            )
            
            # Return the token data
            return TrayAuthResponse(
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                expires_in=token_data.get("expires_in", 3600),
                token_type=token_data.get("token_type", "Bearer")
            )
        except httpx.HTTPError as e:
            raise HTTPException(status_code=400, detail=f"Failed to get token: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get("/tray/refresh-token")
async def refresh_tray_token(seller_id: str):
    """Refresh the access token using refresh token"""
    # Get stored tokens
    stored_tokens = token_service.get_tokens(seller_id)
    if not stored_tokens or "refresh_token" not in stored_tokens:
        raise HTTPException(status_code=400, detail="No refresh token found for seller")
    
    refresh_token = stored_tokens["refresh_token"]
    api_address = stored_tokens.get("api_address", settings.TRAY_API_BASE_URL)
    
    # Make refresh request
    refresh_url = f"{api_address}/auth?refresh_token={refresh_token}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(refresh_url)
            response.raise_for_status()
            token_data = response.json()
            
            # Update stored tokens
            token_service.store_tokens(
                seller_id,
                {
                    "access_token": token_data["access_token"],
                    "refresh_token": token_data["refresh_token"],
                    "expires_in": token_data.get("expires_in", 3600),
                    "token_type": token_data.get("token_type", "Bearer"),
                    "api_address": api_address
                }
            )
            
            return token_data
        except httpx.HTTPError as e:
            raise HTTPException(status_code=400, detail=f"Failed to refresh token: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
