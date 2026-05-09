from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    DATABASE_URL: str = Field(..., description="Async SQLAlchemy DB URL (asyncpg)")
    DATABASE_URL_SYNC: str = Field(..., description="Sync SQLAlchemy DB URL (psycopg2) for Alembic")
    SECRET_KEY: str = Field(..., description="JWT secret key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    PLATFORM_FEE_PERCENT: float = 3.0
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_BUCKET_PORTFOLIOS: str = "portfolios"
    SUPABASE_BUCKET_DELIVERABLES: str = "deliverables"
    DEMO_USERS_ENABLED: bool = False
    DEMO_CUSTOMER_EMAIL: str = ""
    DEMO_CUSTOMER_PASSWORD: str = ""
    DEMO_EXECUTOR_EMAIL: str = ""
    DEMO_EXECUTOR_PASSWORD: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
