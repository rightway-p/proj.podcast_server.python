from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application runtime configuration sourced from environment variables."""

    database_url: str = "sqlite:///./automation_service.db"
    castopod_database_url: str | None = None
    castopod_db_host: str | None = None
    castopod_db_port: int = 3306
    castopod_db_username: str | None = None
    castopod_db_password: str | None = None
    castopod_db_name: str | None = None
    pipeline_command: str = "pipeline-run"
    pipeline_workdir: str | None = None
    pipeline_log_path: str | None = None
    cors_allow_origins: str | None = None

    model_config = SettingsConfigDict(
        env_prefix="automation_",
        env_file=".env",
        env_file_encoding="utf-8",
    )


def get_settings() -> Settings:
    return Settings()
