"""Application configuration"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env from project root (3 levels up from this file: core -> app -> backend -> nba-data)
_project_root = Path(__file__).resolve().parent.parent.parent.parent
_env = _project_root / ".env"
load_dotenv(_env)

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "NBA Data API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "nba_data"
    DUCKDB_PATH: str = "./analytics/nba_analytics.db"
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]
    NBA_API_RATE_LIMIT: int = 590
    NBA_API_DELAY: float = 1.0

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    class Config:
        env_file = str(_env)
        case_sensitive = True

settings = Settings()