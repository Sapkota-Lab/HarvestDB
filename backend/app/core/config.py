from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CropCapture API"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    testing_database_url: str = "postgresql+psycopg://myuser:testing_password@localhost:5432/testing_db"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/cropcapture"
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 60

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")



settings = Settings()
