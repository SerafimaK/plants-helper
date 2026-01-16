"""Репозиторий для работы с базой данных."""

import aiosqlite
from datetime import date, datetime
from typing import Optional

from bot.config import settings
from bot.database.models import (
    Notification,
    NotificationStatus,
    NotificationType,
    PlantStatus,
    SoilMoisture,
    UserSettings,
)


class Database:
    """Класс для работы с SQLite."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(settings.db_path)

    async def init(self):
        """Инициализация базы данных."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript("""
                CREATE TABLE IF NOT EXISTS plant_status (
                    plant_id TEXT PRIMARY KEY,
                    last_moisture TEXT NOT NULL,
                    last_check_date TEXT NOT NULL,
                    next_check_date TEXT NOT NULL,
                    overdue_days INTEGER DEFAULT 0,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plant_id TEXT NOT NULL,
                    notification_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message_id INTEGER,
                    created_at TEXT NOT NULL,
                    answered_at TEXT,
                    answer TEXT
                );

                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id INTEGER PRIMARY KEY,
                    notification_time TEXT NOT NULL DEFAULT '09:00',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_notifications_status 
                ON notifications(status);
                
                CREATE INDEX IF NOT EXISTS idx_notifications_date 
                ON notifications(created_at);
            """)
            await db.commit()

    # Plant Status methods
    async def get_plant_status(self, plant_id: str) -> Optional[PlantStatus]:
        """Получить статус растения."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM plant_status WHERE plant_id = ?", (plant_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return PlantStatus(
                        plant_id=row["plant_id"],
                        last_moisture=SoilMoisture(row["last_moisture"]),
                        last_check_date=date.fromisoformat(row["last_check_date"]),
                        next_check_date=date.fromisoformat(row["next_check_date"]),
                        overdue_days=row["overdue_days"],
                        updated_at=datetime.fromisoformat(row["updated_at"]),
                    )
        return None

    async def get_all_plant_statuses(self) -> list[PlantStatus]:
        """Получить статусы всех растений."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM plant_status") as cursor:
                rows = await cursor.fetchall()
                return [
                    PlantStatus(
                        plant_id=row["plant_id"],
                        last_moisture=SoilMoisture(row["last_moisture"]),
                        last_check_date=date.fromisoformat(row["last_check_date"]),
                        next_check_date=date.fromisoformat(row["next_check_date"]),
                        overdue_days=row["overdue_days"],
                        updated_at=datetime.fromisoformat(row["updated_at"]),
                    )
                    for row in rows
                ]

    async def upsert_plant_status(self, status: PlantStatus):
        """Обновить или создать статус растения."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO plant_status 
                    (plant_id, last_moisture, last_check_date, next_check_date, overdue_days, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(plant_id) DO UPDATE SET
                    last_moisture = excluded.last_moisture,
                    last_check_date = excluded.last_check_date,
                    next_check_date = excluded.next_check_date,
                    overdue_days = excluded.overdue_days,
                    updated_at = excluded.updated_at
                """,
                (
                    status.plant_id,
                    status.last_moisture.value,
                    status.last_check_date.isoformat(),
                    status.next_check_date.isoformat(),
                    status.overdue_days,
                    status.updated_at.isoformat(),
                ),
            )
            await db.commit()

    async def increment_overdue_days(self, plant_id: str):
        """Увеличить счётчик дней игнора."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE plant_status 
                SET overdue_days = overdue_days + 1, updated_at = ?
                WHERE plant_id = ?
                """,
                (datetime.now().isoformat(), plant_id),
            )
            await db.commit()

    async def reset_overdue_days(self, plant_id: str):
        """Сбросить счётчик дней игнора."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE plant_status 
                SET overdue_days = 0, updated_at = ?
                WHERE plant_id = ?
                """,
                (datetime.now().isoformat(), plant_id),
            )
            await db.commit()

    # Notification methods
    async def create_notification(self, notification: Notification) -> int:
        """Создать уведомление."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO notifications 
                    (plant_id, notification_type, status, message_id, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    notification.plant_id,
                    notification.notification_type.value,
                    notification.status.value,
                    notification.message_id,
                    notification.created_at.isoformat(),
                ),
            )
            await db.commit()
            return cursor.lastrowid

    async def update_notification(
        self,
        notification_id: int,
        status: NotificationStatus,
        answer: str = None,
    ):
        """Обновить статус уведомления."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE notifications 
                SET status = ?, answered_at = ?, answer = ?
                WHERE id = ?
                """,
                (
                    status.value,
                    datetime.now().isoformat() if answer else None,
                    answer,
                    notification_id,
                ),
            )
            await db.commit()

    async def update_notification_message_id(self, notification_id: int, message_id: int):
        """Обновить message_id уведомления."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE notifications SET message_id = ? WHERE id = ?",
                (message_id, notification_id),
            )
            await db.commit()

    async def get_pending_notifications(self, for_date: date = None) -> list[Notification]:
        """Получить неотвеченные уведомления."""
        if for_date is None:
            for_date = date.today()

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT * FROM notifications 
                WHERE status IN (?, ?) 
                AND DATE(created_at) = ?
                """,
                (
                    NotificationStatus.PENDING.value,
                    NotificationStatus.REMINDED.value,
                    for_date.isoformat(),
                ),
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    Notification(
                        id=row["id"],
                        plant_id=row["plant_id"],
                        notification_type=NotificationType(row["notification_type"]),
                        status=NotificationStatus(row["status"]),
                        message_id=row["message_id"],
                        created_at=datetime.fromisoformat(row["created_at"]),
                        answered_at=(
                            datetime.fromisoformat(row["answered_at"])
                            if row["answered_at"]
                            else None
                        ),
                        answer=row["answer"],
                    )
                    for row in rows
                ]

    async def get_notification_by_message_id(self, message_id: int) -> Optional[Notification]:
        """Получить уведомление по message_id."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM notifications WHERE message_id = ?", (message_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return Notification(
                        id=row["id"],
                        plant_id=row["plant_id"],
                        notification_type=NotificationType(row["notification_type"]),
                        status=NotificationStatus(row["status"]),
                        message_id=row["message_id"],
                        created_at=datetime.fromisoformat(row["created_at"]),
                        answered_at=(
                            datetime.fromisoformat(row["answered_at"])
                            if row["answered_at"]
                            else None
                        ),
                        answer=row["answer"],
                    )
        return None

    async def get_today_notification_for_plant(
        self, plant_id: str, notification_type: NotificationType = None
    ) -> Optional[Notification]:
        """Получить уведомление для растения за сегодня."""
        today = date.today()
        query = "SELECT * FROM notifications WHERE plant_id = ? AND DATE(created_at) = ?"
        params = [plant_id, today.isoformat()]

        if notification_type:
            query += " AND notification_type = ?"
            params.append(notification_type.value)

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, tuple(params)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return Notification(
                        id=row["id"],
                        plant_id=row["plant_id"],
                        notification_type=NotificationType(row["notification_type"]),
                        status=NotificationStatus(row["status"]),
                        message_id=row["message_id"],
                        created_at=datetime.fromisoformat(row["created_at"]),
                        answered_at=(
                            datetime.fromisoformat(row["answered_at"])
                            if row["answered_at"]
                            else None
                        ),
                        answer=row["answer"],
                    )
        return None

    # User Settings methods
    async def get_user_settings(self, user_id: int) -> Optional[UserSettings]:
        """Получить настройки пользователя."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM user_settings WHERE user_id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return UserSettings(
                        user_id=row["user_id"],
                        notification_time=row["notification_time"],
                        created_at=datetime.fromisoformat(row["created_at"]),
                        updated_at=datetime.fromisoformat(row["updated_at"]),
                    )
        return None

    async def upsert_user_settings(self, user_settings: UserSettings):
        """Обновить или создать настройки пользователя."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO user_settings (user_id, notification_time, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    notification_time = excluded.notification_time,
                    updated_at = excluded.updated_at
                """,
                (
                    user_settings.user_id,
                    user_settings.notification_time,
                    user_settings.created_at.isoformat(),
                    user_settings.updated_at.isoformat(),
                ),
            )
            await db.commit()


# Глобальный экземпляр
db = Database()
