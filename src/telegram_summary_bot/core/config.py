from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    telegram_bot_token: str = Field(alias="TELEGRAM_BOT_TOKEN")
    telegram_base_url: str = Field(
        default="https://api.telegram.org/bot",
        alias="TELEGRAM_BASE_URL",
    )
    telegram_base_file_url: str = Field(
        default="https://api.telegram.org/file/bot",
        alias="TELEGRAM_BASE_FILE_URL",
    )
    llm_api_key: str = Field(alias="LLM_API_KEY")
    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")
    llm_api_base_url: str = Field(
        default="https://api.openai.com/v1",
        alias="LLM_API_BASE_URL",
    )
    outbound_proxy_url: str | None = Field(default=None, alias="OUTBOUND_PROXY_URL")
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/telegram_summary_bot.db",
        alias="DATABASE_URL",
    )
    retention_days: int = Field(default=7, alias="RETENTION_DAYS", ge=1, le=365)
    app_timezone: str = Field(default="Asia/Tehran", alias="APP_TIMEZONE")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    cleanup_interval_seconds: int = Field(
        default=3600,
        alias="CLEANUP_INTERVAL_SECONDS",
        ge=60,
        le=86400,
    )
    summary_max_messages: int = Field(
        default=1500,
        alias="SUMMARY_MAX_MESSAGES",
        ge=10,
        le=10000,
    )
    summary_max_input_chars: int = Field(
        default=120000,
        alias="SUMMARY_MAX_INPUT_CHARS",
        ge=1000,
        le=500000,
    )
    llm_request_timeout_seconds: float = Field(
        default=120.0,
        alias="LLM_REQUEST_TIMEOUT_SECONDS",
        ge=5.0,
        le=600.0,
    )

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        return value.upper()

    def ensure_data_dir(self) -> None:
        if self.database_url.startswith("sqlite"):
            db_path = self.database_url.split("///", maxsplit=1)[-1]
            path = Path(db_path)
            if not path.is_absolute():
                path = Path.cwd() / path
            path.parent.mkdir(parents=True, exist_ok=True)
