"""Обработчики команд."""

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from bot.config import settings
from bot.keyboards.inline import get_main_menu_keyboard

router = Router()


def owner_only(handler):
    """Декоратор для проверки, что сообщение от владельца."""
    async def wrapper(message: Message, **kwargs):
        if message.from_user.id != settings.owner_user_id:
            await message.answer("⛔ У вас нет доступа к этому боту.")
            return
        return await handler(message)
    return wrapper


@router.message(CommandStart())
@owner_only
async def cmd_start(message: Message):
    """Обработчик команды /start."""
    await message.answer(
        "🌱 <b>Привет!</b>\n\n"
        "Я помогу тебе ухаживать за твоими растениями.\n"
        "Буду напоминать о поливе и проверке почвы.\n\n"
        "Выбери действие:",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML",
    )


@router.message(Command("menu"))
@owner_only
async def cmd_menu(message: Message):
    """Обработчик команды /menu."""
    await message.answer(
        "📋 <b>Главное меню</b>",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML",
    )


@router.message(Command("help"))
@owner_only
async def cmd_help(message: Message):
    """Обработчик команды /help."""
    await message.answer(
        "🌱 <b>Plants Helper</b> — бот для ухода за растениями\n\n"
        "<b>Как это работает:</b>\n"
        "• Каждый день в установленное время я присылаю уведомления\n"
        "• Для каждого растения спрашиваю о влажности почвы\n"
        "• На основе твоих ответов планирую следующую проверку\n"
        "• Если почва сухая — напомню полить\n\n"
        "<b>Команды:</b>\n"
        "/start — начало работы\n"
        "/menu — главное меню\n"
        "/help — эта справка\n\n"
        "<b>Условные обозначения:</b>\n"
        "💧💧 — очень влажная почва\n"
        "💧 — слегка влажная\n"
        "🏜 — сухая почва\n"
        "‼️ — срочный полив (игнор > 2 дней)",
        parse_mode="HTML",
    )
