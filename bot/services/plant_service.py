"""Сервис для работы с растениями."""

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from bot.config import settings
from bot.database.models import (
    NotificationStatus,
    NotificationType,
    Plant,
    PlantStatus,
    SoilMoisture,
    WateringPreference,
)
from bot.database.repository import db


class PlantService:
    """Сервис для работы с растениями."""

    def __init__(self):
        self._plants: dict[str, Plant] = {}
        self._loaded = False

    def _load_plants(self):
        """Загрузить профили растений из JSON."""
        if self._loaded:
            return

        plants_file = settings.data_dir / "plants.json"
        if not plants_file.exists():
            self._plants = {}
            self._loaded = True
            return

        with open(plants_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        for plant_data in data.get("plants", []):
            plant = Plant(
                id=plant_data["id"],
                name=plant_data["name"],
                photo=plant_data["photo"],
                check_interval_days=plant_data["check_interval_days"],
                wet_interval_days=plant_data["wet_interval_days"],
                moist_interval_days=plant_data["moist_interval_days"],
                preference=WateringPreference(plant_data["preference"]),
                notes=plant_data.get("notes"),
            )
            self._plants[plant.id] = plant

        self._loaded = True

    def reload_plants(self):
        """Перезагрузить растения из файла."""
        self._loaded = False
        self._plants = {}
        self._load_plants()

    def get_all_plants(self) -> list[Plant]:
        """Получить все растения."""
        self._load_plants()
        return list(self._plants.values())

    def get_plant(self, plant_id: str) -> Optional[Plant]:
        """Получить растение по ID."""
        self._load_plants()
        return self._plants.get(plant_id)

    def get_plant_photo_path(self, plant: Plant) -> Path:
        """Получить путь к фото растения."""
        return settings.base_dir / plant.photo

    async def get_or_create_status(self, plant_id: str) -> PlantStatus:
        """Получить или создать статус растения."""
        status = await db.get_plant_status(plant_id)
        if status is None:
            # Создаём начальный статус — проверка сегодня
            status = PlantStatus(
                plant_id=plant_id,
                last_moisture=SoilMoisture.DRY,
                last_check_date=date.today(),
                next_check_date=date.today(),
                overdue_days=0,
            )
            await db.upsert_plant_status(status)
        return status

    async def calculate_next_check_date(
        self, plant: Plant, moisture: SoilMoisture
    ) -> date:
        """Рассчитать следующую дату проверки."""
        today = date.today()

        if moisture == SoilMoisture.WATERED:
            return today + timedelta(days=plant.check_interval_days)
        elif moisture == SoilMoisture.VERY_WET:
            return today + timedelta(days=plant.wet_interval_days)
        elif moisture == SoilMoisture.SLIGHTLY_WET:
            return today + timedelta(days=plant.moist_interval_days)
        else:  # DRY
            if plant.preference == WateringPreference.UNDERWATER:
                # Лучше пересушить — напоминаем завтра
                return today + timedelta(days=1)
            else:
                # Лучше недополить — напоминаем сегодня
                return today

    async def process_moisture_answer(
        self, plant_id: str, moisture: SoilMoisture
    ) -> tuple[date, Optional[str]]:
        """
        Обработать ответ о влажности почвы.
        
        Returns:
            tuple[date, Optional[str]]: (следующая дата проверки, сообщение)
        """
        plant = self.get_plant(plant_id)
        if not plant:
            raise ValueError(f"Plant {plant_id} not found")

        next_check = await self.calculate_next_check_date(plant, moisture)

        # Обновляем статус
        status = PlantStatus(
            plant_id=plant_id,
            last_moisture=moisture,
            last_check_date=date.today(),
            next_check_date=next_check,
            overdue_days=0,  # Сбрасываем при ответе
        )
        await db.upsert_plant_status(status)

        # Формируем сообщение
        message = None
        if moisture == SoilMoisture.DRY:
            if plant.preference == WateringPreference.OVERWATER:
                message = f"🚿 Пожалуйста, полей {plant.name}!"
            else:
                message = f"📅 Напомню полить {plant.name} завтра"

        return next_check, message

    async def process_watering_done(self, plant_id: str) -> date:
        """Обработать подтверждение полива."""
        plant = self.get_plant(plant_id)
        if not plant:
            raise ValueError(f"Plant {plant_id} not found")

        next_check = date.today() + timedelta(days=plant.check_interval_days)

        status = PlantStatus(
            plant_id=plant_id,
            last_moisture=SoilMoisture.WATERED,
            last_check_date=date.today(),
            next_check_date=next_check,
            overdue_days=0,
        )
        await db.upsert_plant_status(status)
        await db.reset_overdue_days(plant_id)

        return next_check

    async def get_plants_for_today(
        self,
    ) -> tuple[list[tuple[Plant, PlantStatus]], list[tuple[Plant, PlantStatus]]]:
        """
        Получить растения для сегодняшних уведомлений.
        
        Returns:
            tuple: (растения для проверки, растения для полива)
        """
        self._load_plants()
        today = date.today()

        to_check = []
        to_water = []

        for plant in self._plants.values():
            status = await self.get_or_create_status(plant.id)

            if status.next_check_date <= today:
                # Проверяем, нужен ли полив
                if (
                    status.last_moisture == SoilMoisture.DRY
                    and status.overdue_days > 0
                ):
                    to_water.append((plant, status))
                else:
                    to_check.append((plant, status))

        return to_check, to_water

    async def reschedule_unanswered(self):
        """Перенести неотвеченные уведомления на завтра."""
        today = date.today()
        tomorrow = today + timedelta(days=1)

        pending = await db.get_pending_notifications(today)

        for notification in pending:
            # Обновляем статус уведомления
            await db.update_notification(
                notification.id, NotificationStatus.RESCHEDULED
            )

            # Обновляем дату следующей проверки
            status = await db.get_plant_status(notification.plant_id)
            if status:
                # Увеличиваем счётчик игнора для уведомлений о поливе
                if notification.notification_type == NotificationType.WATER:
                    await db.increment_overdue_days(notification.plant_id)

                # Переносим на завтра
                status.next_check_date = tomorrow
                status.updated_at = datetime.now()
                await db.upsert_plant_status(status)


# Глобальный экземпляр
plant_service = PlantService()
