"""Конфигурация бота."""

from pathlib import Path

from pydantic import field_validator
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

    # Telegram - пользователи
    admin_user_ids: list[int]  # Список ID админов (через запятую в .env)
    admin_names: str  # Имена админов через запятую (в том же порядке)
    active_waterer_id: int  # ID активного поливальщика (получает уведомления)

    @field_validator("admin_user_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        """Парсит строку ID через запятую в список."""
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        return v

    @property
    def admin_names_map(self) -> dict[int, str]:
        """Словарь user_id -> имя."""
        names = [n.strip() for n in self.admin_names.split(",")]
        return dict(zip(self.admin_user_ids, names))

    def get_admin_name(self, user_id: int) -> str:
        """Получить имя админа по ID."""
        return self.admin_names_map.get(user_id, f"User {user_id}")

    def is_admin(self, user_id: int) -> bool:
        """Проверить, является ли пользователь админом."""
        return user_id in self.admin_user_ids

    # Google Sheets
    google_sheets_enabled: bool = False
    google_sheets_credentials_file: str = "credentials.json"
    google_sheets_credentials_base64: str = ""  # Альтернатива файлу — base64 encoded JSON
    google_sheets_spreadsheet_id: str = ""

    # Timing (фиксированное)
    notification_time: str = "10:00"  # Утренние уведомления
    reminder_time: str = "18:00"  # Напоминания о неотвеченных

    # Timezone
    timezone: str = "Europe/Moscow"

    # Paths
    base_dir: Path = _BASE_DIR
    data_dir: Path = _BASE_DIR / "data"
    images_dir: Path = _BASE_DIR / "images"
    db_path: Path = _BASE_DIR / "data" / "plants.db"


settings = Settings()
