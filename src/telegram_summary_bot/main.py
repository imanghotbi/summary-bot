from __future__ import annotations

from telegram_summary_bot.bootstrap.application import build_application, register_handlers
from telegram_summary_bot.core.config import Settings
from telegram_summary_bot.core.logging import configure_logging


def main() -> None:
    settings = Settings()
    configure_logging(settings.log_level)

    application = build_application(settings)
    application.bot_data["settings"] = settings
    register_handlers(application)
    application.run_polling(
        allowed_updates=None,
        drop_pending_updates=False,
    )


if __name__ == "__main__":
    main()
