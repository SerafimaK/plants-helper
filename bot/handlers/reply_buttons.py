"""Обработчики Reply кнопок (кнопки под полем ввода)."""

from aiogram import F, Router
from aiogram.types import Message

from bot.config import settings
from bot.keyboards.inline import (
    get_admin_plants_list_keyboard,
    get_main_menu_keyboard,
    get_plants_list_keyboard,
    get_settings_keyboard,
)
from bot.keyboards.reply import get_main_reply_keyboard
from bot.services.plant_service import plant_service

router = Router()


def owner_only(handler):
    """Декоратор для проверки, что сообщение от владельца."""
    async def wrapper(message: Message, **kwargs):
        if message.from_user.id != settings.owner_user_id:
            await message.answer("⛔ У вас нет доступа к этому боту.")
            return
        return await handler(message)
    return wrapper


@router.message(F.text == "🌱 Мои растения")
@owner_only
async def btn_plants(message: Message):
    """Обработчик кнопки 'Мои растения'."""
    plants = plant_service.get_all_plants()

    if not plants:
        await message.answer(
            "🌱 <b>Мои растения</b>\n\n"
            "Пока нет ни одного растения.\n"
            "Добавь их в файл <code>data/plants.json</code>",
            reply_markup=get_main_reply_keyboard(),
        )
    else:
        await message.answer(
            f"🌱 <b>Мои растения</b> ({len(plants)})\n\n"
            "Выбери растение для просмотра:",
            reply_markup=get_plants_list_keyboard(plants),
        )


@router.message(F.text == "🔧 Управление")
@owner_only
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


@router.message(F.text == "⚙️ Настройки")
@owner_only
async def btn_settings(message: Message):
    """Обработчик кнопки 'Настройки'."""
    await message.answer(
        "⚙️ <b>Настройки</b>",
        reply_markup=get_settings_keyboard(),
    )


@router.message(F.text == "❓ Помощь")
@owner_only
async def btn_help(message: Message):
    """Обработчик кнопки 'Помощь'."""
    await message.answer(
        "🌱 <b>Plants Helper</b> — бот для ухода за растениями\n\n"
        "<b>Как это работает:</b>\n"
        "• Каждый день в установленное время я присылаю уведомления\n"
        "• Для каждого растения спрашиваю о влажности почвы\n"
        "• На основе твоих ответов планирую следующую проверку\n"
        "• Если почва сухая — напомню полить\n\n"
        "<b>Кнопки меню:</b>\n"
        "🌱 Мои растения — список и информация\n"
        "🔧 Управление — ручное обновление статуса\n"
        "⚙️ Настройки — время уведомлений\n\n"
        "<b>Условные обозначения:</b>\n"
        "💧💧 — очень влажная почва\n"
        "💧 — слегка влажная\n"
        "🏜 — сухая почва\n"
        "‼️ — срочный полив (игнор > 2 дней)",
    )
