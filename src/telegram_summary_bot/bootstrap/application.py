from __future__ import annotations

from telegram.ext import Application, ApplicationBuilder, CommandHandler, MessageHandler, filters

from telegram_summary_bot.core.config import Settings
from telegram_summary_bot.handlers.commands import help_command, start_command, summary_command
from telegram_summary_bot.handlers.errors import on_error
from telegram_summary_bot.handlers.messages import store_group_message
from telegram_summary_bot.infrastructure.lifecycle import post_init, post_shutdown


def build_application(settings: Settings) -> Application:
    return (
        ApplicationBuilder()
        .token(settings.telegram_bot_token)
        .base_url(settings.telegram_base_url)
        .base_file_url(settings.telegram_base_file_url)
        .concurrent_updates(True)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )


def register_handlers(application: Application) -> None:
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("summary", summary_command))
    application.add_handler(
        MessageHandler(
            filters.ChatType.GROUPS & ~filters.StatusUpdate.ALL,
            store_group_message,
        )
    )
    application.add_error_handler(on_error)
