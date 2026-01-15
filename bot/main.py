"""Точка входа бота."""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import settings
from bot.database.repository import db
from bot.handlers import (
    admin_router,
    callbacks_router,
    commands_router,
    menu_router,
    plants_router,
    settings_router,
)
from bot.services.plant_service import plant_service
from bot.services.scheduler import notification_scheduler
from bot.services.sheets import sheets_service

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot):
    """Действия при запуске бота."""
    logger.info("Инициализация базы данных...")
    await db.init()

    logger.info("Инициализация Google Sheets...")
    await sheets_service.init()

    # Инициализируем растения в таблице
    plants = plant_service.get_all_plants()
    await sheets_service.init_plants([p.name for p in plants])

    logger.info("Запуск планировщика...")
    notification_scheduler.set_bot(bot)
    await notification_scheduler.start()

    # Уведомление о запуске
    try:
        await bot.send_message(
            settings.owner_user_id,
            "🌱 <b>Plants Helper запущен!</b>\n\n"
            "Используй /menu для открытия меню.",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.warning(f"Не удалось отправить сообщение о запуске: {e}")

    logger.info("Бот запущен!")


async def on_shutdown(bot: Bot):
    """Действия при остановке бота."""
    logger.info("Остановка планировщика...")
    notification_scheduler.stop()

    logger.info("Бот остановлен.")


async def main():
    """Главная функция."""
    # Создаём бота
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Создаём диспетчер
    dp = Dispatcher()

    # Регистрируем роутеры
    dp.include_router(commands_router)
    dp.include_router(menu_router)
    dp.include_router(admin_router)
    dp.include_router(plants_router)
    dp.include_router(settings_router)
    dp.include_router(callbacks_router)

    # Регистрируем хуки
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Запускаем polling
    logger.info("Запуск бота...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
