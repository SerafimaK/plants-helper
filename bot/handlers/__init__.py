"""Handlers package."""

from bot.handlers.admin import router as admin_router
from bot.handlers.callbacks import router as callbacks_router
from bot.handlers.commands import router as commands_router
from bot.handlers.menu import router as menu_router
from bot.handlers.plants import router as plants_router
from bot.handlers.settings import router as settings_router

__all__ = [
    "admin_router",
    "callbacks_router",
    "commands_router",
    "menu_router",
    "plants_router",
    "settings_router",
]
