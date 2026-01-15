"""Обработчики callback-кнопок уведомлений."""

from datetime import date

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.database.models import NotificationStatus, SoilMoisture
from bot.database.repository import db
from bot.keyboards.inline import (
    get_answered_keyboard,
    get_moisture_keyboard,
    get_watering_keyboard,
)
from bot.services.plant_service import plant_service
from bot.services.sheets import sheets_service

router = Router()


@router.callback_query(F.data.startswith("moisture:"))
async def handle_moisture_answer(callback: CallbackQuery):
    """Обработка ответа о влажности почвы."""
    parts = callback.data.split(":")
    plant_id = parts[1]
    moisture_value = parts[2]

    plant = plant_service.get_plant(plant_id)
    if not plant:
        await callback.answer("Растение не найдено", show_alert=True)
        return

    # Маппинг значений
    moisture_map = {
        "very_wet": SoilMoisture.VERY_WET,
        "slightly_wet": SoilMoisture.SLIGHTLY_WET,
        "dry": SoilMoisture.DRY,
    }
    moisture = moisture_map.get(moisture_value)

    if not moisture:
        await callback.answer("Неверное значение", show_alert=True)
        return

    # Обрабатываем ответ
    next_check, message = await plant_service.process_moisture_answer(plant_id, moisture)

    # Обновляем уведомление в БД
    notification = await db.get_notification_by_message_id(callback.message.message_id)
    if notification:
        await db.update_notification(
            notification.id, NotificationStatus.ANSWERED, moisture_value
        )

    # Логируем в Google Sheets
    await sheets_service.mark_answered(plant.name, _format_moisture_short(moisture_value))
    await sheets_service.mark_scheduled(plant.name, next_check)

    # Формируем текст ответа
    answer_text = _format_moisture(moisture_value)
    
    # Если сухая и полив нужен сегодня — сразу отправляем уведомление о поливе
    today = date.today()
    if moisture == SoilMoisture.DRY and next_check == today:
        await callback.message.edit_text(
            f"🌱 <b>{plant.name}</b>\n\n"
            f"Ответ: {answer_text}",
            reply_markup=get_answered_keyboard(plant_id, answer_text),
            parse_mode="HTML",
        )
        
        # Отправляем уведомление о поливе
        await callback.message.answer(
            f"🚿 <b>{plant.name}</b>\n\n"
            f"Почва сухая — пожалуйста, полей цветок!",
            reply_markup=get_watering_keyboard(plant_id),
            parse_mode="HTML",
        )
        await callback.answer("Нужен полив!")
        return

    response_text = (
        f"🌱 <b>{plant.name}</b>\n\n"
        f"Ответ: {answer_text}\n"
        f"📅 Следующая проверка: {next_check.strftime('%d.%m.%Y')}"
    )

    if message:
        response_text += f"\n\n{message}"

    # Обновляем сообщение
    await callback.message.edit_text(
        response_text,
        reply_markup=get_answered_keyboard(plant_id, answer_text),
        parse_mode="HTML",
    )
    await callback.answer("Ответ сохранён!")


@router.callback_query(F.data.startswith("watered:"))
async def handle_watered(callback: CallbackQuery):
    """Обработка подтверждения полива."""
    plant_id = callback.data.split(":")[1]

    plant = plant_service.get_plant(plant_id)
    if not plant:
        await callback.answer("Растение не найдено", show_alert=True)
        return

    # Обрабатываем полив
    next_check = await plant_service.process_watering_done(plant_id)

    # Обновляем уведомление в БД
    notification = await db.get_notification_by_message_id(callback.message.message_id)
    if notification:
        await db.update_notification(
            notification.id, NotificationStatus.ANSWERED, "watered"
        )

    # Логируем в Google Sheets
    await sheets_service.mark_answered(plant.name, "✅")
    await sheets_service.mark_scheduled(plant.name, next_check)

    # Обновляем сообщение
    await callback.message.edit_text(
        f"🌱 <b>{plant.name}</b>\n\n"
        f"✅ Отлично, полито!\n"
        f"📅 Следующая проверка: {next_check.strftime('%d.%m.%Y')}",
        reply_markup=get_answered_keyboard(plant_id, "Полито"),
        parse_mode="HTML",
    )
    await callback.answer("Отлично! 🌱")


@router.callback_query(F.data.startswith("correct:"))
async def handle_correct_answer(callback: CallbackQuery):
    """Исправление ответа."""
    plant_id = callback.data.split(":")[1]

    plant = plant_service.get_plant(plant_id)
    if not plant:
        await callback.answer("Растение не найдено", show_alert=True)
        return

    # Определяем тип уведомления по предыдущему сообщению
    notification = await db.get_notification_by_message_id(callback.message.message_id)

    if notification and notification.answer == "watered":
        # Было уведомление о поливе
        keyboard = get_watering_keyboard(plant_id)
        text = f"🚿 <b>{plant.name}</b>\n\nПожалуйста, полей цветок!"
    else:
        # Было уведомление о проверке
        keyboard = get_moisture_keyboard(plant_id)
        text = f"🌱 <b>{plant.name}</b>\n\nКак сегодня почва?"

    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await callback.answer("Выбери новый ответ")


def _format_moisture(moisture: str) -> str:
    """Форматировать влажность для отображения."""
    mapping = {
        "very_wet": "💧💧 Очень влажная",
        "slightly_wet": "💧 Слегка влажная",
        "dry": "🏜 Сухая",
    }
    return mapping.get(moisture, moisture)


def _format_moisture_short(moisture: str) -> str:
    """Короткий формат влажности для таблицы."""
    mapping = {
        "very_wet": "💧💧",
        "slightly_wet": "💧",
        "dry": "🏜",
    }
    return mapping.get(moisture, moisture)
