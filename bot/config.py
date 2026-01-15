"""Конфигурация бота."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Telegram
    bot_token: str
    owner_user_id: int

    # Google Sheets
    google_sheets_enabled: bool = False
    google_sheets_credentials_file: str = "credentials.json"
    google_sheets_spreadsheet_id: str = ""

    # Timing
    default_notification_time: str = "09:00"
    reminder_time: str = "18:00"

    # Timezone
    timezone: str = "Europe/Moscow"

    # Paths
    base_dir: Path = Path(__file__).parent.parent
    data_dir: Path = base_dir / "data"
    images_dir: Path = base_dir / "images"
    db_path: Path = base_dir / "data" / "plants.db"


settings = Settings()
