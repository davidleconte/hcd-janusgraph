"""
Centralised Settings
====================

Single source of truth for all environment configuration.
Uses pydantic-settings so every value is validated at startup.

Environment-specific configuration:
- Development: loads .env.development (SSL disabled)
- Production: loads .env (SSL enabled)

Usage:
    from src.python.config.settings import get_settings
    settings = get_settings()
    print(settings.janusgraph_host)
"""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _get_env_file() -> str:
    """Determine which .env file to load based on environment.
    
    Priority:
    1. .env.development (if ENVIRONMENT=development or file exists)
    2. .env (fallback for production)
    
    Returns:
        Path to the env file to load.
    """
    env = os.getenv("ENVIRONMENT", "development")
    
    # For development, prefer .env.development
    if env == "development" and os.path.exists(".env.development"):
        return ".env.development"
    
    # Fallback to .env (production or if .env.development doesn't exist)
    return ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=_get_env_file(),
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
    opensearch_verify_certs: bool = True
    opensearch_ca_certs: Optional[str] = None
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
    log_sanitization: bool = Field(
        True,
        description="Apply PII log sanitization filter when True",
    )
    log_redact_ip: bool = Field(
        False,
        description="Redact IP addresses when log sanitization is enabled",
    )

    @field_validator("log_level")
    @classmethod
    def _upper_log_level(cls, v: str) -> str:
        return v.upper()

    @property
    def janusgraph_ws_url(self) -> str:
        """Return the WebSocket URL for JanusGraph Gremlin server.

        Returns:
            WebSocket URL string (ws:// or wss://).
        """
        protocol = "wss" if self.janusgraph_use_ssl else "ws"
        return f"{protocol}://{self.janusgraph_host}:{self.janusgraph_port}/gremlin"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins string into a list.

        Returns:
            List of allowed CORS origin URLs.
        """
        if self.api_cors_origins == "*":
            return ["*"]
        return [o.strip() for o in self.api_cors_origins.split(",")]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached Settings singleton."""
    return Settings()
