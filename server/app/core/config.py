"""Application Configuration"""

from functools import lru_cache
from typing import Any, List, Literal, Union

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=(
            "env",
            "env.development",
            ".env",
            ".env.development",
            "server/.env",
            "server/.env.development",
            "../env.development",
            "../env",
        ),
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        case_sensitive=False,
        extra="ignore",
        # Disable JSON schema validation for env vars to allow comma-separated strings
        json_schema_extra={"env_nested_delimiter": "__"},
    )

    # Application
    APP_NAME: str = "Panda Tales API"
    APP_ENV: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True
    API_VERSION: str = "v1"
    SECRET_KEY: str = Field(..., min_length=32)
    ALLOWED_ORIGINS: Union[str, List[str]] = Field(
        default="http://localhost:3000"
    )

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: PostgresDsn
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_ECHO: bool = False

    # JWT
    JWT_SECRET_KEY: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # OAuth - Google
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""

    # Storage
    STORAGE_PROVIDER: Literal["s3", "r2"] = "r2"

    # Cloudflare R2 (S3-compatible)
    R2_ENDPOINT: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET: str = "pandatales"
    R2_SECURE: bool = True
    R2_VERIFY_SSL: bool = True
    R2_REGION: str = "auto"
    R2_PUBLIC_BASE_URL: str = ""

    # AWS S3 (alternative)
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    S3_BUCKET: str = "pandatales-files"

    # Celery (Optional)
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_MAX_TOKENS: int = 2000

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # Razorpay
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""
    RAZORPAY_VERIFY_SSL: bool = True

    # Replicate AI (image generation)
    REPLICATE_API_TOKEN: str = ""
    REPLICATE_MODEL_VERSION: str = "467d062309da518648ba89d226490e02b8ed09b5abc15026e54e31c5a8cd0769"
    MAX_PARALLEL_GENERATIONS: int = 2  # max concurrent Replicate predictions per book
    TEST_PAGE_LIMIT: int | None = 2  # Set to None to disable, or number to limit pages for testing
    REPLICATE_STAGGER_SECONDS: float = 5.0  # Delay between prediction starts to avoid rate limiting
    REPLICATE_MAX_RETRIES: int = 3  # Reduced from 6 to minimize log noise

    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@pandatales.com"
    SMTP_FROM_NAME: str = "Panda Tales"
    SELLER_GSTIN: str = "33BEEPN5284A1ZS"
    GST_INTRA_STATE_BY_DEFAULT: bool = False

    # Local digital order delivery
    LOCAL_DIGITAL_DELIVERY_DIR: str = "local-deliveries/digital-orders"

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000

    # File Limits
    MAX_FILE_SIZE_AVATAR: int = 5_242_880  # 5MB
    MAX_FILE_SIZE_PHOTO: int = 10_485_760  # 10MB
    MAX_FILE_SIZE_PDF: int = 52_428_800  # 50MB

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: Literal["json", "text"] = "json"

    # Monitoring
    SENTRY_DSN: str = ""
    SENTRY_ENVIRONMENT: str = "development"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.APP_ENV == "development"

    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL for Alembic"""
        return str(self.DATABASE_URL).replace("+asyncpg", "")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
