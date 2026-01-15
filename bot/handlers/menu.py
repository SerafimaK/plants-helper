"""Обработчики главного меню."""

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.keyboards.inline import (
    get_main_menu_keyboard,
    get_plants_list_keyboard,
    get_settings_keyboard,
)
from bot.services.plant_service import plant_service

router = Router()


@router.callback_query(F.data == "menu:main")
async def menu_main(callback: CallbackQuery):
    """Главное меню."""
    await callback.message.edit_text(
        "📋 <b>Главное меню</b>",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "menu:plants")
async def menu_plants(callback: CallbackQuery):
    """Меню растений."""
    plants = plant_service.get_all_plants()

    if not plants:
        await callback.message.edit_text(
            "🌱 <b>Мои растения</b>\n\n"
            "Пока нет ни одного растения.\n"
            "Добавь их в файл <code>data/plants.json</code>",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML",
        )
    else:
        await callback.message.edit_text(
            f"🌱 <b>Мои растения</b> ({len(plants)})\n\n"
            "Выбери растение для просмотра:",
            reply_markup=get_plants_list_keyboard(plants),
            parse_mode="HTML",
        )

    await callback.answer()


@router.callback_query(F.data == "menu:settings")
async def menu_settings(callback: CallbackQuery):
    """Меню настроек."""
    await callback.message.edit_text(
        "⚙️ <b>Настройки</b>",
        reply_markup=get_settings_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop_handler(callback: CallbackQuery):
    """Пустой обработчик для неактивных кнопок."""
    await callback.answer()
