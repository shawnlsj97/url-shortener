from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_environment: str = "development"
    database_url: str = "sqlite:///./var/ogp.db"
    public_base_url: str = "http://localhost:8000"
    session_token_pepper: str = "development-only-change-me"
    session_cookie_name: str = "ogp_session"
    csrf_cookie_name: str = "ogp_csrf"
    session_lifetime_days: int = 14


@lru_cache
def get_settings() -> Settings:
    return Settings()
