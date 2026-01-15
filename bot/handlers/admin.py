"""Админка для управления состояниями растений."""

from datetime import date

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.database.models import SoilMoisture
from bot.config import settings
from bot.keyboards.inline import (
    get_admin_keyboard,
    get_admin_plant_keyboard,
    get_admin_plants_list_keyboard,
    get_watering_keyboard,
)
from bot.services.plant_service import plant_service
from bot.services.sheets import sheets_service

router = Router()


@router.callback_query(F.data == "menu:admin")
async def menu_admin(callback: CallbackQuery):
    """Меню администрирования."""
    plants = plant_service.get_all_plants()
    statuses = []

    for plant in plants:
        status = await plant_service.get_or_create_status(plant.id)
        statuses.append((plant, status))

    # Сортируем по дате следующей проверки
    statuses.sort(key=lambda x: x[1].next_check_date)

    text = "🔧 <b>Управление растениями</b>\n\n"
    text += "<b>Текущие статусы:</b>\n"

    for plant, status in statuses:
        emoji = _moisture_emoji(status.last_moisture)
        next_check = status.next_check_date.strftime("%d.%m")
        text += f"{emoji} {plant.name} → {next_check}\n"

    text += "\nВыбери растение для изменения статуса:"

    await callback.message.edit_text(
        text,
        reply_markup=get_admin_plants_list_keyboard(plants),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:plant:"))
async def admin_plant(callback: CallbackQuery):
    """Управление конкретным растением."""
    plant_id = callback.data.split(":")[2]

    plant = plant_service.get_plant(plant_id)
    if not plant:
        await callback.answer("Растение не найдено", show_alert=True)
        return

    status = await plant_service.get_or_create_status(plant_id)

    text = (
        f"🌱 <b>{plant.name}</b>\n\n"
        f"<b>Текущий статус:</b>\n"
        f"💧 Влажность: {_moisture_text(status.last_moisture)}\n"
        f"📅 Последняя проверка: {status.last_check_date.strftime('%d.%m.%Y')}\n"
        f"📆 Следующая проверка: {status.next_check_date.strftime('%d.%m.%Y')}\n"
    )

    if status.overdue_days > 0:
        text += f"⚠️ Дней без полива: {status.overdue_days}\n"

    text += "\n<b>Установить новый статус:</b>"

    await callback.message.edit_text(
        text,
        reply_markup=get_admin_plant_keyboard(plant_id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:set:"))
async def admin_set_status(callback: CallbackQuery):
    """Установить статус растения."""
    parts = callback.data.split(":")
    plant_id = parts[2]
    moisture_value = parts[3]

    plant = plant_service.get_plant(plant_id)
    if not plant:
        await callback.answer("Растение не найдено", show_alert=True)
        return

    # Маппинг значений
    moisture_map = {
        "watered": SoilMoisture.WATERED,
        "very_wet": SoilMoisture.VERY_WET,
        "slightly_wet": SoilMoisture.SLIGHTLY_WET,
        "dry": SoilMoisture.DRY,
    }
    moisture = moisture_map.get(moisture_value)

    if not moisture:
        await callback.answer("Неверное значение", show_alert=True)
        return

    # Обрабатываем изменение статуса
    if moisture == SoilMoisture.WATERED:
        next_check = await plant_service.process_watering_done(plant_id)
        await sheets_service.mark_answered(plant.name, "✅")
    else:
        next_check, _ = await plant_service.process_moisture_answer(plant_id, moisture)
        await sheets_service.mark_answered(plant.name, _moisture_emoji(moisture))

    # Отмечаем запланированную дату в таблице
    await sheets_service.mark_scheduled(plant.name, next_check)

    # Если сухая и полив нужен сегодня — сразу отправляем уведомление
    today = date.today()
    if moisture == SoilMoisture.DRY and next_check == today:
        await callback.message.edit_text(
            f"✅ <b>Статус обновлён</b>\n\n"
            f"🌱 {plant.name}\n"
            f"💧 Новый статус: {_moisture_text(moisture)}",
            reply_markup=get_admin_keyboard(),
            parse_mode="HTML",
        )
        
        # Отправляем уведомление о поливе
        await callback.message.answer(
            f"🚿 <b>{plant.name}</b>\n\n"
            f"Почва сухая — пожалуйста, полей цветок!",
            reply_markup=get_watering_keyboard(plant_id),
            parse_mode="HTML",
        )
        await callback.answer("Отправлено уведомление о поливе!")
        return

    await callback.message.edit_text(
        f"✅ <b>Статус обновлён</b>\n\n"
        f"🌱 {plant.name}\n"
        f"💧 Новый статус: {_moisture_text(moisture)}\n"
        f"📆 Следующая проверка: {next_check.strftime('%d.%m.%Y')}",
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer("Статус сохранён!")


def _moisture_emoji(moisture: SoilMoisture) -> str:
    """Эмодзи для влажности."""
    mapping = {
        SoilMoisture.WATERED: "✅",
        SoilMoisture.VERY_WET: "💧💧",
        SoilMoisture.SLIGHTLY_WET: "💧",
        SoilMoisture.DRY: "🏜",
    }
    return mapping.get(moisture, "❓")


def _moisture_text(moisture: SoilMoisture) -> str:
    """Текст для влажности."""
    mapping = {
        SoilMoisture.WATERED: "✅ Полито сегодня",
        SoilMoisture.VERY_WET: "💧💧 Очень влажная",
        SoilMoisture.SLIGHTLY_WET: "💧 Слегка влажная",
        SoilMoisture.DRY: "🏜 Сухая",
    }
    return mapping.get(moisture, str(moisture))
