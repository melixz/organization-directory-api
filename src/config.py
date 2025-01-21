from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    API_KEY: str
    SECRET_KEY: str = "super-secret-key"
    APP_NAME: str = "Organization Directory API"
    DEBUG: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
