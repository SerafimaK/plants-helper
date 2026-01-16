"""Планировщик уведомлений."""

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from bot.config import settings
from bot.database.models import (
    Notification,
    NotificationStatus,
    NotificationType,
)
from bot.database.repository import db
from bot.services.plant_service import plant_service
from bot.services.sheets import sheets_service

if TYPE_CHECKING:
    from aiogram import Bot

logger = logging.getLogger(__name__)


def _parse_time(time_str: str) -> tuple[int, int]:
    """Безопасный парсинг времени HH:MM."""
    parts = time_str.split(":")
    if len(parts) >= 2:
        return int(parts[0]), int(parts[1])
    # Fallback: если только часы
    return int(parts[0]), 0


class NotificationScheduler:
    """Планировщик уведомлений о поливе."""

    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone=pytz.timezone(settings.timezone))
        self.bot: "Bot" = None
        self._notification_job_id = "daily_notifications"
        self._reminder_job_id = "daily_reminders"
        self._reschedule_job_id = "daily_reschedule"

    def set_bot(self, bot: "Bot"):
        """Установить экземпляр бота."""
        self.bot = bot

    async def start(self):
        """Запустить планировщик."""
        # Парсим фиксированное время из конфига
        hour, minute = _parse_time(settings.notification_time)
        reminder_hour, reminder_minute = _parse_time(settings.reminder_time)

        # Ежедневные уведомления в 10:00
        self.scheduler.add_job(
            self._send_daily_notifications,
            CronTrigger(hour=hour, minute=minute),
            id=self._notification_job_id,
            replace_existing=True,
        )

        # Напоминания о неотвеченных в 18:00
        self.scheduler.add_job(
            self._send_reminders,
            CronTrigger(hour=reminder_hour, minute=reminder_minute),
            id=self._reminder_job_id,
            replace_existing=True,
        )

        # Перенос неотвеченных в конце дня (23:59)
        self.scheduler.add_job(
            self._reschedule_unanswered,
            CronTrigger(hour=23, minute=59),
            id=self._reschedule_job_id,
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info(
            f"Планировщик запущен. Уведомления в {settings.notification_time}, "
            f"напоминания в {settings.reminder_time}"
        )

    def stop(self):
        """Остановить планировщик."""
        self.scheduler.shutdown()

    async def run_daily_check(self):
        """Запустить ежедневную проверку (например, при старте)."""
        await self._send_daily_notifications()

    async def _send_daily_notifications(self) -> tuple[int, int]:
        """Отправить ежедневные уведомления."""
        if not self.bot:
            logger.error("Bot not set")
            return 0, 0

        logger.info("Отправка ежедневных уведомлений...")

        to_check, to_water = await plant_service.get_plants_for_today()
        sent_check = 0
        sent_water = 0

        # Импортируем здесь, чтобы избежать циклического импорта
        from bot.keyboards.inline import get_moisture_keyboard, get_watering_keyboard

        # Отправляем уведомления о проверке активному поливальщику
        for plant, status in to_check:
            # Проверяем, не отправляли ли уже сегодня
            existing = await db.get_today_notification_for_plant(
                plant.id, NotificationType.CHECK
            )
            if existing:
                continue

            try:
                keyboard = get_moisture_keyboard(plant.id)
                message = await self.bot.send_message(
                    settings.active_waterer_id,
                    f"🌱 <b>{plant.name}</b>\n\nКак сегодня почва?",
                    reply_markup=keyboard,
                    parse_mode="HTML",
                )

                # Сохраняем уведомление
                notification = Notification(
                    id=None,
                    plant_id=plant.id,
                    notification_type=NotificationType.CHECK,
                    status=NotificationStatus.PENDING,
                    message_id=message.message_id,
                    created_at=datetime.now(),
                )
                await db.create_notification(notification)
                await sheets_service.mark_sent(plant.name)
                sent_check += 1

            except Exception as e:
                logger.error(f"Ошибка отправки уведомления для {plant.name}: {e}")

        # Отправляем уведомления о поливе
        for plant, status in to_water:
            # Проверяем, не отправляли ли уже сегодня
            existing = await db.get_today_notification_for_plant(
                plant.id, NotificationType.WATER
            )
            if existing:
                continue

            try:
                # Добавляем ‼️ если игнор > 2 дней
                urgent = status.overdue_days >= 2
                emoji = "‼️ " if urgent else ""

                keyboard = get_watering_keyboard(plant.id)
                text = (
                    f"{emoji}🚿 <b>{plant.name}</b>\n\n"
                    f"{'Срочно полей!' if urgent else 'Пожалуйста, полей цветок!'}"
                )

                if urgent:
                    text += f"\n\n⚠️ Без полива уже {status.overdue_days} дней"

                message = await self.bot.send_message(
                    settings.active_waterer_id,
                    text,
                    reply_markup=keyboard,
                    parse_mode="HTML",
                )

                notification = Notification(
                    id=None,
                    plant_id=plant.id,
                    notification_type=NotificationType.WATER,
                    status=NotificationStatus.PENDING,
                    message_id=message.message_id,
                    created_at=datetime.now(),
                )
                await db.create_notification(notification)
                await sheets_service.mark_sent(plant.name)
                sent_water += 1

            except Exception as e:
                logger.error(f"Ошибка отправки уведомления о поливе для {plant.name}: {e}")

        logger.info(
            f"Отправлено уведомлений: {sent_check} проверок, {sent_water} поливов"
        )
        return sent_check, sent_water

    async def _send_reminders(self) -> int:
        """Отправить напоминания о неотвеченных уведомлениях."""
        if not self.bot:
            return 0

        logger.info("Проверка неотвеченных уведомлений...")

        pending = await db.get_pending_notifications()
        pending_not_reminded = [
            n for n in pending if n.status == NotificationStatus.PENDING
        ]

        if not pending_not_reminded:
            logger.info("Все уведомления отвечены")
            return 0

        sent_count = 0
        for notification in pending_not_reminded:
            try:
                plant = plant_service.get_plant(notification.plant_id)
                if not plant:
                    continue

                # Отправляем напоминание активному поливальщику
                await self.bot.send_message(
                    settings.active_waterer_id,
                    f"⏰ Напоминание: ты ещё не ответил про <b>{plant.name}</b>",
                    parse_mode="HTML",
                )

                # Обновляем статус
                await db.update_notification(
                    notification.id, NotificationStatus.REMINDED
                )
                sent_count += 1

            except Exception as e:
                logger.error(f"Ошибка отправки напоминания: {e}")

        logger.info(f"Отправлено {sent_count} напоминаний")
        return sent_count

    async def _reschedule_unanswered(self):
        """Перенести неотвеченные уведомления на завтра."""
        logger.info("Перенос неотвеченных уведомлений...")
        await plant_service.reschedule_unanswered()
        logger.info("Неотвеченные уведомления перенесены на завтра")


# Глобальный экземпляр
notification_scheduler = NotificationScheduler()
