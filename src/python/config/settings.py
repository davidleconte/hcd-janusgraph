"""
Centralised Settings
====================

Single source of truth for all environment configuration.
Uses pydantic-settings so every value is validated at startup.

Usage:
    from src.python.config.settings import get_settings
    settings = get_settings()
    print(settings.janusgraph_host)
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: str = Field("development", description="Runtime environment")
    debug: bool = False

    janusgraph_host: str = "localhost"
    janusgraph_port: int = 18182
    janusgraph_use_ssl: bool = False
    janusgraph_ca_certs: Optional[str] = None

    opensearch_host: str = "localhost"
    opensearch_port: int = 9200
    opensearch_use_ssl: bool = False
    opensearch_username: Optional[str] = None
    opensearch_password: Optional[str] = None

    pulsar_url: str = "pulsar://localhost:6650"

    api_host: str = "0.0.0.0"
    api_port: int = 8001
    api_key: str = ""
    api_jwt_secret: str = ""
    api_access_token_ttl_minutes: int = 15
    api_refresh_token_ttl_minutes: int = 1440
    api_user: str = "admin"
    api_user_password: str = ""
    api_user_roles: str = "admin"
    api_user_email: str = "admin@localhost"
    auth_enabled: bool = False
    auth_default_roles: str = "user"
    mfa_required_roles: str = "admin,developer"
    api_cors_origins: str = "http://localhost:3000,http://localhost:8080"

    rate_limit_per_minute: int = Field(60, description="Requests per minute per client")

    otel_service_name: str = "janusgraph-client"
    jaeger_host: str = "localhost"
    jaeger_port: int = 6831
    tracing_enabled: bool = True
    tracing_sample_rate: float = 1.0

    log_level: str = "INFO"
    log_json: bool = Field(False, description="Emit structured JSON logs when True")

    @field_validator("log_level")
    @classmethod
    def _upper_log_level(cls, v: str) -> str:
        return v.upper()

    @property
    def janusgraph_ws_url(self) -> str:
        protocol = "wss" if self.janusgraph_use_ssl else "ws"
        return f"{protocol}://{self.janusgraph_host}:{self.janusgraph_port}/gremlin"

    @property
    def cors_origins_list(self) -> List[str]:
        if self.api_cors_origins == "*":
            return ["*"]
        return [o.strip() for o in self.api_cors_origins.split(",")]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached Settings singleton."""
    return Settings()
