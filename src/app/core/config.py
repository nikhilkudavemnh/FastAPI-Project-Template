"""Application settings. Every service built from this template reads the same schema;
set SERVICE_NAME / ENABLED_MODULES per deployment to turn one image into many services."""

import json
from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

type Environment = Literal["development", "staging", "production", "test"]
type TaskBackendName = Literal["inline", "celery"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    # Identity
    service_name: str = "api"
    environment: Environment = "development"
    debug: bool = False
    log_level: str = "INFO"
    log_json: bool = False
    enabled_modules: Annotated[list[str], NoDecode] = Field(
        default=["auth", "users", "roles", "ai"]
    )

    # HTTP
    api_prefix: str = "/api/v1"
    cors_origins: Annotated[list[str], NoDecode] = Field(default_factory=list)

    # Database
    database_url: str = "postgresql+asyncpg://app:app@localhost:5432/app"
    db_echo: bool = False
    db_pool_size: int = 10

    # Cache / broker
    redis_url: str | None = None

    # Auth
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Bootstrap
    first_superuser_email: str = "admin@example.com"
    first_superuser_password: str = "changeme123"

    # Tasks
    task_backend: TaskBackendName = "inline"

    @field_validator("enabled_modules", "cors_origins", mode="before")
    @classmethod
    def _parse_list(cls, v: object) -> object:
        """Accept JSON arrays or comma-separated strings from the environment."""
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                return json.loads(v)
            return [m.strip() for m in v.split(",") if m.strip()]
        return v

    @field_validator("redis_url", mode="before")
    @classmethod
    def _empty_to_none(cls, v: object) -> object:
        return None if v == "" else v

    @model_validator(mode="after")
    def _production_guardrails(self) -> Settings:
        if self.environment == "production" and (
            self.jwt_secret == "change-me" or len(self.jwt_secret) < 32
        ):
            raise ValueError("JWT_SECRET must be a random string of at least 32 characters")
        return self

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_test(self) -> bool:
        return self.environment == "test"


@lru_cache
def get_settings() -> Settings:
    return Settings()
