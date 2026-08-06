from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://invoice_checker:invoice_checker@localhost:5432/invoice_checker"
    secret_key: str = "dev-secret-key"
    debug: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
