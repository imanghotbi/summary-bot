from __future__ import annotations

from telegram.ext import ContextTypes

from telegram_summary_bot.core.types import AppServices


def get_services(context: ContextTypes.DEFAULT_TYPE) -> AppServices:
    return context.application.bot_data["services"]
