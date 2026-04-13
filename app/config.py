from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    base_dir: Path = Path(__file__).resolve().parents[1]
    api_host: str = Field(default="0.0.0.0", validation_alias="API_HOST")
    api_port: int = Field(default=8010, validation_alias="API_PORT")
    inbound_api_username: str = Field(default="", validation_alias="INBOUND_API_USERNAME")
    inbound_api_password: str = Field(default="", validation_alias="INBOUND_API_PASSWORD")
    disable_inbound_auth: bool = Field(default=False, validation_alias="DISABLE_INBOUND_AUTH")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    data_file: Path = Field(default=Path(__file__).resolve().parents[1] / "data" / "latest_sales.json", validation_alias="DATA_FILE")


settings = Settings()
