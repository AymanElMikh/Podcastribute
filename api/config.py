"""Application configuration via Pydantic Settings.

All environment variables are loaded from the .env file or the shell environment.
Never hardcode credentials — use this module for all config access.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings loaded from environment variables.

    All values have sensible defaults for local development.
    Production deployments must override secrets via environment or .env file.
    """

    # LLM Gateway
    GATEWAY_URL: str = "http://gateway.yourdomain.com"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost/podcastai"

    # Redis / Celery
    REDIS_URL: str = "redis://redis:6379"
    CELERY_BROKER_URL: str = "redis://redis:6379/1"

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_STARTER: str = ""
    STRIPE_PRICE_CREATOR: str = ""
    STRIPE_PRICE_STUDIO: str = ""

    # Audio processing
    WHISPER_MODEL: str = "small"
    UPLOADS_DIR: str = "/uploads"
    MAX_UPLOAD_MB: int = 500

    # Auth
    JWT_SECRET_KEY: str = "changeme"
    JWT_ALGORITHM: str = "HS256"

    # Runtime
    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
