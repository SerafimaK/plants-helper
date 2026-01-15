"""Обработчики настроек."""

from datetime import datetime

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.config import settings
from bot.database.models import UserSettings
from bot.database.repository import db
from bot.keyboards.inline import get_settings_keyboard, get_time_selection_keyboard
from bot.services.scheduler import notification_scheduler

router = Router()


@router.callback_query(F.data == "settings:notification_time")
async def settings_notification_time(callback: CallbackQuery):
    """Выбор времени уведомлений."""
    user_settings = await db.get_user_settings(settings.owner_user_id)
    current_time = (
        user_settings.notification_time
        if user_settings
        else settings.default_notification_time
    )

    await callback.message.edit_text(
        f"🕐 <b>Время уведомлений</b>\n\n"
        f"Текущее время: <b>{current_time}</b>\n\n"
        f"Выбери новое время:",
        reply_markup=get_time_selection_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_time:"))
async def set_notification_time(callback: CallbackQuery):
    """Установить время уведомлений."""
    # set_time:08:00 -> берём всё после первого ":"
    new_time = callback.data.split(":", 1)[1]

    # Сохраняем в БД
    user_settings = UserSettings(
        user_id=settings.owner_user_id,
        notification_time=new_time,
    )
    await db.upsert_user_settings(user_settings)

    # Обновляем планировщик
    await notification_scheduler.update_notification_time(new_time)

    await callback.message.edit_text(
        f"✅ <b>Время уведомлений изменено</b>\n\n"
        f"Новое время: <b>{new_time}</b>\n\n"
        f"Теперь уведомления будут приходить в {new_time}.",
        reply_markup=get_settings_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer("Время сохранено!")
