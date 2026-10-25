
"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration for the API and upstream portal."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    portal_base_url: str = "https://urja-ops.flockenergy.tech"
    portal_email: str = ""
    portal_password: SecretStr = SecretStr("")
    portal_session_cookie: SecretStr = SecretStr("")
    request_timeout: float = Field(default=30.0, gt=0, le=120)
    api_port: int = Field(default=8000, ge=1, le=65535)


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
