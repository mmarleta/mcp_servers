from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    email: Optional[str] = None
    

class TrayAuthRequest(BaseModel):
    code: str
    store_host: str
    api_address: str
    

class TrayAuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "Bearer"
    store_id: Optional[str] = None
    api_host: Optional[str] = None
    

class TrayTokenRefreshRequest(BaseModel):
    refresh_token: str
    api_address: str
