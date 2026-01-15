"""Конфигурация бота."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Вычисляем базовую директорию один раз
_BASE_DIR = Path(__file__).parent.parent.resolve()


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
    google_sheets_credentials_base64: str = ""  # Альтернатива файлу — base64 encoded JSON
    google_sheets_spreadsheet_id: str = ""

    # Timing
    default_notification_time: str = "09:00"
    reminder_time: str = "18:00"

    # Timezone
    timezone: str = "Europe/Moscow"

    # Paths
    base_dir: Path = _BASE_DIR
    data_dir: Path = _BASE_DIR / "data"
    images_dir: Path = _BASE_DIR / "images"
    db_path: Path = _BASE_DIR / "data" / "plants.db"


settings = Settings()
