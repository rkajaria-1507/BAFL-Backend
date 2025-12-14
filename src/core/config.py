"""
Application configuration settings.
Loads environment variables and provides typed configuration.
"""
from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
import json

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"


class Settings(BaseSettings):
    # Application
    APP_NAME: str = Field(...)
    APP_VERSION: str = Field(...)
    DEBUG: bool = Field(...)
    ENVIRONMENT: Literal["development", "staging", "production"] = Field(...)

    # Server
    HOST: str = Field(...)
    PORT: int = Field(...)

    # Security
    SECRET_KEY: str = Field(...)
    ALGORITHM: str = Field(...)
    ACCESS_TOKEN_EXPIRE_DAYS: int = Field(...)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(...)

    # Database
    DATABASE_URL: str = Field(...)

    # CORS
    CORS_ORIGINS: list[str] | str = Field(...)
    CORS_ALLOW_CREDENTIALS: bool = Field(...)
    CORS_ALLOW_METHODS: list[str] | str = Field(...)
    CORS_ALLOW_HEADERS: list[str] | str = Field(...)

    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(...)
    LOG_FORMAT: str = Field(...)

    # Initial Admin
    INITIAL_ADMIN_NAME: str = Field(...)
    INITIAL_ADMIN_USERNAME: str = Field(...)
    INITIAL_ADMIN_PASSWORD: str = Field(...)

    @field_validator('DATABASE_URL', mode='before')
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        if isinstance(v, str):
            # Fix Supabase/Postgres URLs: SQLAlchemy 2.0+ requires postgresql:// not postgres://
            if v.startswith("postgres://"):
                v = v.replace("postgres://", "postgresql://", 1)
            
            # Legacy SQLite support (kept for backward compatibility)
            if v.startswith("sqlite:///"):
                # Extract path/query components to support URLs like sqlite:///./db.sqlite?timeout=10
                path_part, separator, query = v[len("sqlite:///"):].partition("?")

                if path_part and path_part != ":memory:":
                    candidate_path = Path(path_part)
                    if not candidate_path.is_absolute():
                        absolute_path = (BASE_DIR / candidate_path).resolve()
                        normalized = f"sqlite:///{absolute_path.as_posix()}"
                        if separator:
                            normalized = f"{normalized}?{query}"
                        return normalized
        return v

    @field_validator('CORS_ORIGINS', 'CORS_ALLOW_METHODS', 'CORS_ALLOW_HEADERS', mode='before')
    @classmethod
    def parse_cors_list(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return [v]
        return v

    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
