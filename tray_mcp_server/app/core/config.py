from pydantic_settings import BaseSettings
from typing import List, Union
from pydantic import AnyHttpUrl


class Settings(BaseSettings):
    PROJECT_NAME: str = "Tray MCP Server"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    
    # Tray API Configuration
    TRAY_API_BASE_URL: str = "https://www.tray.com.br/web_api"
    TRAY_AUTH_URL: str = "https://www.tray.com.br/web_api/auth"
    TRAY_CONSUMER_KEY: str = ""
    TRAY_CONSUMER_SECRET: str = ""
    
    # Database
    DATABASE_URL: str = "sqlite:///./test.db"
    
    # Redis for token storage
    REDIS_URL: str = "redis://localhost:6379/0"
    
    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
