from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_name: str = "CareerOS API"
    environment: str = "development"
    database_url: str = "sqlite:///./careeros.db"
    jwt_secret: str = "development-secret-change-this-please-32b"
    jwt_refresh_secret: str = "development-refresh-secret-change-32b"
    access_token_minutes: int = 60
    demo_mode: bool = True
    cors_origins: str = "http://localhost:3000"
    upload_dir: str = "./uploads"
    max_upload_mb: int = 5

    @property
    def cors_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


settings = Settings()
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
