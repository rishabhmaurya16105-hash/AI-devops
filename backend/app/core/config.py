from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATABASE_ENV_FILE = PROJECT_ROOT / "database" / ".env"


class Settings(BaseSettings):
    app_name: str = "DevOpsMart API"
    environment: str = "development"
    debug: bool = False
    database_url: SecretStr | None = Field(
        default=None,
        validation_alias="DEVOPSMART_DATABASE_URL",
    )
    postgres_host: str = Field(default="127.0.0.1", validation_alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, validation_alias="POSTGRES_PORT")
    postgres_db: str = Field(default="devopsmart", validation_alias="POSTGRES_DB")
    postgres_user: str = Field(default="devopsmart", validation_alias="POSTGRES_USER")
    postgres_password: SecretStr = Field(
        default=SecretStr(""),
        validation_alias="POSTGRES_PASSWORD",
    )

    model_config = SettingsConfigDict(
        env_prefix="DEVOPSMART_",
        env_file=DATABASE_ENV_FILE,
        extra="ignore",
    )


settings = Settings()
