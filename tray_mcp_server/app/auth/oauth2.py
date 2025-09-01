from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import os
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception

def get_current_user(token: str = Depends(oauth2_scheme)):
    # 🧪 MODO DE DESENVOLVIMENTO - Bypass de autenticação
    dev_mode = os.getenv("DEV_MODE", "false").lower() == "true"
    dev_tokens = [
        "dev_token_bypass_auth_for_testing",
        "development_token",
        "test_token",
        "bypass_auth"
    ]
    
    # Se estiver em modo dev OU usando token de desenvolvimento
    if dev_mode or token in dev_tokens:
        print(f"🧪 DEV MODE: Bypassing authentication with token: {token[:20]}...")
        return {
            "sub": "dev_user@test.com",
            "user_id": "dev_user_123",
            "seller_id": "dev_seller_456",
            "mode": "development",
            "permissions": ["read", "write", "admin"]
        }
    
    # Autenticação normal para produção
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return verify_token(token, credentials_exception)
