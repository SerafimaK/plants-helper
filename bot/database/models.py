"""Модели данных."""

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Optional


class SoilMoisture(str, Enum):
    """Состояние влажности почвы."""

    WATERED = "watered"  # сегодня полили
    VERY_WET = "very_wet"  # очень влажная
    SLIGHTLY_WET = "slightly_wet"  # слегка влажная
    DRY = "dry"  # сухая


class NotificationStatus(str, Enum):
    """Статус уведомления."""

    PENDING = "pending"  # отправлено, ждём ответа
    REMINDED = "reminded"  # напоминание отправлено
    ANSWERED = "answered"  # пользователь ответил
    RESCHEDULED = "rescheduled"  # перенесено на следующий день


class NotificationType(str, Enum):
    """Тип уведомления."""

    CHECK = "check"  # проверка влажности
    WATER = "water"  # просьба полить


class WateringPreference(str, Enum):
    """Предпочтение: пересушить или перелить."""

    UNDERWATER = "underwater"  # лучше пересушить
    OVERWATER = "overwater"  # лучше недополить


@dataclass
class Plant:
    """Профиль растения (из JSON)."""

    id: str
    name: str
    photo: str
    check_interval_days: int  # через сколько дней проверять после полива
    wet_interval_days: int  # через сколько дней проверять, если очень влажная
    moist_interval_days: int  # через сколько дней проверять, если слегка влажная
    preference: WateringPreference
    notes: Optional[str] = None


@dataclass
class PlantStatus:
    """Текущий статус растения (в БД)."""

    plant_id: str
    last_moisture: SoilMoisture
    last_check_date: date
    next_check_date: date
    overdue_days: int = 0  # дней игнора просьбы полить
    updated_at: datetime = None

    def __post_init__(self):
        if self.updated_at is None:
            self.updated_at = datetime.now()


@dataclass
class Notification:
    """Уведомление (в БД)."""

    id: Optional[int]
    plant_id: str
    notification_type: NotificationType
    status: NotificationStatus
    message_id: Optional[int]  # ID сообщения в Telegram
    created_at: datetime
    answered_at: Optional[datetime] = None
    answer: Optional[str] = None  # ответ пользователя


@dataclass
class UserSettings:
    """Настройки пользователя."""

    user_id: int
    notification_time: str = "09:00"
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        now = datetime.now()
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now
