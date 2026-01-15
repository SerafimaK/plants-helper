"""Inline клавиатуры."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="🔧 Управление растениями", callback_data="menu:admin")
    )
    builder.row(
        InlineKeyboardButton(text="🌱 Мои растения", callback_data="menu:plants")
    )
    builder.row(
        InlineKeyboardButton(text="⚙️ Настройки", callback_data="menu:settings")
    )

    return builder.as_markup()


def get_moisture_keyboard(plant_id: str) -> InlineKeyboardMarkup:
    """Клавиатура для вопроса о влажности почвы."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="💧💧 Очень влажная", callback_data=f"moisture:{plant_id}:very_wet"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="💧 Немного влажная", callback_data=f"moisture:{plant_id}:slightly_wet"
        )
    )
    builder.row(
        InlineKeyboardButton(text="🏜 Сухая", callback_data=f"moisture:{plant_id}:dry")
    )
    builder.row(
        InlineKeyboardButton(
            text="🖼 Как выглядит цветок?", callback_data=f"show_photo:{plant_id}"
        )
    )

    return builder.as_markup()


def get_watering_keyboard(plant_id: str) -> InlineKeyboardMarkup:
    """Клавиатура для просьбы полить."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="✅ Готово!", callback_data=f"watered:{plant_id}")
    )
    builder.row(
        InlineKeyboardButton(
            text="🖼 Как выглядит цветок?", callback_data=f"show_photo:{plant_id}"
        )
    )

    return builder.as_markup()


def get_answered_keyboard(plant_id: str, answer_text: str) -> InlineKeyboardMarkup:
    """Клавиатура после ответа (с кнопкой исправления)."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text=f"✓ {answer_text}", callback_data="noop")
    )
    builder.row(
        InlineKeyboardButton(
            text="↩️ Исправить ответ", callback_data=f"correct:{plant_id}"
        )
    )

    return builder.as_markup()


def get_plants_list_keyboard(plants: list) -> InlineKeyboardMarkup:
    """Клавиатура со списком растений."""
    builder = InlineKeyboardBuilder()

    for plant in plants:
        builder.row(
            InlineKeyboardButton(
                text=f"🌱 {plant.name}", callback_data=f"plant_info:{plant.id}"
            )
        )

    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main")
    )

    return builder.as_markup()


def get_plant_info_keyboard(plant_id: str) -> InlineKeyboardMarkup:
    """Клавиатура для информации о растении."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="🖼 Показать фото", callback_data=f"show_photo:{plant_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(text="◀️ К списку", callback_data="menu:plants")
    )

    return builder.as_markup()


def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура настроек."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="🕐 Время уведомлений", callback_data="settings:notification_time"
        )
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main")
    )

    return builder.as_markup()


def get_time_selection_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора времени."""
    builder = InlineKeyboardBuilder()

    times = [
        ("🌅 08:00", "08:00"),
        ("🌄 09:00", "09:00"),
        ("☀️ 10:00", "10:00"),
        ("🌇 18:00", "18:00"),
        ("🌆 19:00", "19:00"),
        ("🌃 20:00", "20:00"),
        ("🌙 21:00", "21:00"),
    ]

    for label, time_value in times:
        builder.row(
            InlineKeyboardButton(
                text=label, callback_data=f"set_time:{time_value}"
            )
        )

    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="menu:settings")
    )

    return builder.as_markup()


def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Кнопка возврата в меню."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="◀️ В меню", callback_data="menu:main")
    )
    return builder.as_markup()


# === Админка ===

def get_admin_plants_list_keyboard(plants: list) -> InlineKeyboardMarkup:
    """Клавиатура со списком растений для админки."""
    builder = InlineKeyboardBuilder()

    for plant in plants:
        builder.row(
            InlineKeyboardButton(
                text=f"🌱 {plant.name}", callback_data=f"admin:plant:{plant.id}"
            )
        )

    builder.row(
        InlineKeyboardButton(text="◀️ В меню", callback_data="menu:main")
    )

    return builder.as_markup()


def get_admin_plant_keyboard(plant_id: str) -> InlineKeyboardMarkup:
    """Клавиатура для управления статусом растения."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="✅ Полито сегодня", callback_data=f"admin:set:{plant_id}:watered"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="💧💧 Очень влажная", callback_data=f"admin:set:{plant_id}:very_wet"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="💧 Слегка влажная", callback_data=f"admin:set:{plant_id}:slightly_wet"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🏜 Сухая", callback_data=f"admin:set:{plant_id}:dry"
        )
    )
    builder.row(
        InlineKeyboardButton(text="◀️ К списку", callback_data="menu:admin")
    )

    return builder.as_markup()


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура после действия в админке."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="🔧 К списку растений", callback_data="menu:admin")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ В меню", callback_data="menu:main")
    )

    return builder.as_markup()
