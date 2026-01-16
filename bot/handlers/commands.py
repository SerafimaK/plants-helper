"""Обработчики команд."""

from datetime import datetime
import pytz
from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from bot.config import settings
from bot.keyboards.inline import get_main_menu_keyboard
from bot.keyboards.reply import get_main_reply_keyboard
from bot.services.scheduler import notification_scheduler

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


@router.message(Command("debug_time"))
@admin_only
async def cmd_debug_time(message: Message):
    """Отладка времени и настроек."""
    server_time = datetime.now()
    utc_time = datetime.now(pytz.utc)
    
    try:
        tz = pytz.timezone(settings.timezone)
        tz_time = datetime.now(tz)
    except Exception as e:
        tz_time = f"Error: {e}"
    
    jobs = notification_scheduler.scheduler.get_jobs()
    jobs_str = "\n".join([f"- {job.id}: {job.next_run_time} (TZ: {job.next_run_time.tzinfo})" for job in jobs]) if jobs else "Нет активных задач"
    
    text = (
        f"🕒 <b>Time Debug</b>\n\n"
        f"Server Time: {server_time}\n"
        f"UTC Time: {utc_time}\n"
        f"Config Timezone: {settings.timezone}\n"
        f"Time in Config TZ: {tz_time}\n\n"
        f"<b>Settings:</b>\n"
        f"Notification Time: {settings.notification_time}\n"
        f"Reminder Time: {settings.reminder_time}\n\n"
        f"<b>Scheduled Jobs:</b>\n"
        f"{jobs_str}"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("trigger_check"))
@admin_only
async def cmd_trigger_check(message: Message):
    """Принудительный запуск ежедневной проверки."""
    await message.answer("🔄 Запускаю проверку уведомлений...")
    try:
        check, water = await notification_scheduler._send_daily_notifications()
        await message.answer(f"✅ Проверка завершена.\nОтправлено: {check} проверок, {water} поливов.")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


@router.message(Command("trigger_reminders"))
@admin_only
async def cmd_trigger_reminders(message: Message):
    """Принудительный запуск напоминаний."""
    await message.answer("🔄 Запускаю проверку напоминаний...")
    try:
        count = await notification_scheduler._send_reminders()
        await message.answer(f"✅ Готово. Отправлено напоминаний: {count}")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
