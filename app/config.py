from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_WEBHOOK_URL: str
    TELEGRAM_AUTHORIZED_USERNAME: str

    LLM_CLIENT_MODEL: str
    LLM_CLIENT_API_KEY: str
    LLM_CLIENT_BASE_URL: str

    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: str

    NAVASAN_API_KEY: str

    SERPAPI_API_KEY: str

    DIGIN_MAX_RESULTS: int

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
