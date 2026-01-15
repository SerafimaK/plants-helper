"""Обработчики для работы с растениями."""

from aiogram import F, Router
from aiogram.types import CallbackQuery, FSInputFile

from bot.keyboards.inline import get_plant_info_keyboard, get_plants_list_keyboard
from bot.services.plant_service import plant_service

router = Router()


@router.callback_query(F.data.startswith("plant_info:"))
async def plant_info(callback: CallbackQuery):
    """Показать информацию о растении."""
    plant_id = callback.data.split(":")[1]
    plant = plant_service.get_plant(plant_id)

    if not plant:
        await callback.answer("Растение не найдено", show_alert=True)
        return

    # Получаем статус растения
    status = await plant_service.get_or_create_status(plant_id)

    text = (
        f"🌱 <b>{plant.name}</b>\n\n"
        f"📅 Интервал проверки: {plant.check_interval_days} дн.\n"
        f"💧 Если очень влажная: +{plant.wet_interval_days} дн.\n"
        f"💧 Если слегка влажная: +{plant.moist_interval_days} дн.\n"
        f"🎯 Предпочтение: {'пересушить' if plant.preference.value == 'underwater' else 'недополить'}\n"
    )

    if plant.notes:
        text += f"\n📝 {plant.notes}\n"

    text += (
        f"\n<b>Текущий статус:</b>\n"
        f"📊 Последняя влажность: {_format_moisture(status.last_moisture.value)}\n"
        f"📆 Следующая проверка: {status.next_check_date.strftime('%d.%m.%Y')}"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_plant_info_keyboard(plant_id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("show_photo:"))
async def show_photo(callback: CallbackQuery):
    """Показать фото растения."""
    plant_id = callback.data.split(":")[1]
    plant = plant_service.get_plant(plant_id)

    if not plant:
        await callback.answer("Растение не найдено", show_alert=True)
        return

    photo_path = plant_service.get_plant_photo_path(plant)

    if not photo_path.exists():
        await callback.answer(
            f"Фото не найдено: {plant.photo}",
            show_alert=True,
        )
        return

    # Отправляем фото отдельным сообщением (не редактируем текущее)
    photo = FSInputFile(photo_path)
    await callback.message.answer_photo(
        photo,
        caption=f"🌱 <b>{plant.name}</b>",
        parse_mode="HTML",
    )
    await callback.answer()


def _format_moisture(moisture: str) -> str:
    """Форматировать влажность для отображения."""
    mapping = {
        "watered": "💧 Полито",
        "very_wet": "💧💧 Очень влажная",
        "slightly_wet": "💧 Слегка влажная",
        "dry": "🏜 Сухая",
    }
    return mapping.get(moisture, moisture)
