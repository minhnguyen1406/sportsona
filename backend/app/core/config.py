from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Sportsona"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # Deploy environment. The startup secret-key guard in main.py refuses
    # to boot with the in-code dev default when this is anything other
    # than "development".
    ENVIRONMENT: str = "development"

    # Public-facing API URL. When set (e.g. "https://api.sportsona.com")
    # it populates the OpenAPI `servers` field so generated clients use HTTPS.
    API_BASE_URL: str = ""

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "sportsona_user"
    POSTGRES_PASSWORD: str = "dev_password_123"
    POSTGRES_DB: str = "sportsona"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

    # JWT
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # short-lived; clients refresh before this expires
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # FastF1
    FASTF1_CACHE_DIR: str = "/app/cache"

    # Frontend URL — used to build links inside email-verification and
    # password-reset emails. Must be set per-environment in production.
    FRONTEND_URL: str = "http://localhost:5173"

    # Anthropic / race recaps
    ANTHROPIC_API_KEY: str = ""
    RECAP_MODEL: str = "claude-opus-4-7"
    RECAP_MAX_OUTPUT_TOKENS: int = 1500

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
