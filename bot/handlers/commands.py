"""Обработчики команд."""

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from bot.config import settings
from bot.keyboards.inline import get_main_menu_keyboard
from bot.keyboards.reply import get_main_reply_keyboard

router = Router()


def admin_only(handler):
    """Декоратор для проверки, что сообщение от одного из админов."""
    async def wrapper(message: Message, **kwargs):
        if not settings.is_admin(message.from_user.id):
            await message.answer("⛔ У вас нет доступа к этому боту.")
            return
        return await handler(message)
    return wrapper


@router.message(CommandStart())
@admin_only
async def cmd_start(message: Message):
    """Обработчик команды /start."""
    user_name = settings.get_admin_name(message.from_user.id)
    is_waterer = message.from_user.id == settings.active_waterer_id
    waterer_info = " 🚿 Ты сейчас активный поливальщик!" if is_waterer else ""
    
    await message.answer(
        f"🌱 <b>Привет, {user_name}!</b>{waterer_info}\n\n"
        "Я помогу тебе ухаживать за растениями.\n"
        "Буду напоминать о поливе и проверке почвы.\n\n"
        "Используй кнопки меню внизу 👇",
        reply_markup=get_main_reply_keyboard(),
        parse_mode="HTML",
    )


@router.message(Command("menu"))
@admin_only
async def cmd_menu(message: Message):
    """Обработчик команды /menu."""
    await message.answer(
        "📋 <b>Меню</b>\n\n"
        "Используй кнопки внизу 👇",
        reply_markup=get_main_reply_keyboard(),
        parse_mode="HTML",
    )


