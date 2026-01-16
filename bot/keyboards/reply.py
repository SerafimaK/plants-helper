"""Reply клавиатуры (кнопки под полем ввода)."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_main_reply_keyboard() -> ReplyKeyboardMarkup:
    """Главная клавиатура с постоянными кнопками."""
    builder = ReplyKeyboardBuilder()

    builder.row(
        KeyboardButton(text="🖼 Как выглядит..."),
        KeyboardButton(text="🔧 Управление"),
    )
    builder.row(
        KeyboardButton(text="🌱 Все растения"),
    )

    return builder.as_markup(resize_keyboard=True, is_persistent=True)
