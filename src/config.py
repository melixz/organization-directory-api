from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "organization_db")
    DATABASE_HOST: str = os.getenv("DATABASE_HOST", "localhost")
    DATABASE_PORT: int = int(os.getenv("DATABASE_PORT", 5432))
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"postgresql+asyncpg://{os.getenv('POSTGRES_USER', 'user')}:"
        f"{os.getenv('POSTGRES_PASSWORD', 'password')}@"
        f"{os.getenv('DATABASE_HOST', 'localhost')}:"
        f"{os.getenv('DATABASE_PORT', 5432)}/"
        f"{os.getenv('POSTGRES_DB', 'organization_db')}",
    )
    API_KEY: str = os.getenv("API_KEY", "default-api-key")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key")
    APP_NAME: str = os.getenv("APP_NAME", "Organization Directory API")
    DEBUG: bool = bool(int(os.getenv("DEBUG", 0)))

    class Config:
        env_file = ".env"


settings = Settings()
