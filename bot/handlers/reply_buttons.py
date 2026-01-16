"""Обработчики Reply кнопок (кнопки под полем ввода)."""

from aiogram import F, Router
from aiogram.types import Message

from bot.config import settings
from bot.keyboards.inline import (
    get_admin_plants_list_keyboard,
    get_photo_list_keyboard,
    get_plants_list_keyboard,
)
from bot.keyboards.reply import get_main_reply_keyboard
from bot.services.plant_service import plant_service

router = Router()


def admin_only(handler):
    """Декоратор для проверки, что сообщение от одного из админов."""
    async def wrapper(message: Message, **kwargs):
        if not settings.is_admin(message.from_user.id):
            await message.answer("⛔ У вас нет доступа к этому боту.")
            return
        return await handler(message)
    return wrapper


@router.message(F.text == "🖼 Как выглядит...")
@admin_only
async def btn_show_photo(message: Message):
    """Обработчик кнопки 'Как выглядит...'."""
    plants = plant_service.get_all_plants()

    if not plants:
        await message.answer(
            "🖼 <b>Как выглядит...</b>\n\n"
            "Пока нет ни одного растения.\n"
            "Добавь их в файл <code>data/plants.json</code>",
        )
    else:
        await message.answer(
            "🖼 <b>Как выглядит...</b>\n\n"
            "Выбери растение:",
            reply_markup=get_photo_list_keyboard(plants),
        )


@router.message(F.text == "🔧 Управление")
@admin_only
async def btn_admin(message: Message):
    """Обработчик кнопки 'Управление'."""
    plants = plant_service.get_all_plants()

    if not plants:
        await message.answer(
            "🔧 <b>Управление растениями</b>\n\n"
            "Нет растений для управления.\n"
            "Добавь их в файл <code>data/plants.json</code>",
            reply_markup=get_main_reply_keyboard(),
        )
    else:
        await message.answer(
            "🔧 <b>Управление растениями</b>\n\n"
            "Выбери растение:",
            reply_markup=get_admin_plants_list_keyboard(plants),
        )


@router.message(F.text == "🌱 Все растения")
@admin_only
async def btn_plants(message: Message):
    """Обработчик кнопки 'Все растения'."""
    plants = plant_service.get_all_plants()

    if not plants:
        await message.answer(
            "🌱 <b>Все растения</b>\n\n"
            "Пока нет ни одного растения.\n"
            "Добавь их в файл <code>data/plants.json</code>",
        )
    else:
        await message.answer(
            f"🌱 <b>Все растения</b> ({len(plants)})\n\n"
            "Выбери растение для просмотра:",
            reply_markup=get_plants_list_keyboard(plants),
        )
