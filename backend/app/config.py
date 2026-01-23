from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str

    # Azure OpenAI
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_API_VERSION: str = "2024-12-01-preview"
    AZURE_CHAT_DEPLOYMENT: str = "gpt-5.1"
    AZURE_EMBEDDING_DEPLOYMENT: str = "text-embedding-3-large"

    # DingTalk
    DINGTALK_APP_KEY: str
    DINGTALK_APP_SECRET: str

    # Confluence (base URL only, credentials are per-user)
    CONFLUENCE_BASE_URL: str

    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 180  # 180 days

    # Application
    ENVIRONMENT: str = "production"
    CORS_ORIGINS: str = "https://cf.rocktor.shop"
    APP_BASE_URL: str = "https://cf.rocktor.shop"

    class Config:
        env_file = ".env"

settings = Settings()
