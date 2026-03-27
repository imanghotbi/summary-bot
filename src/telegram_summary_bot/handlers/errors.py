from __future__ import annotations

import logging

from telegram.ext import ContextTypes

LOGGER = logging.getLogger(__name__)


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    LOGGER.exception("Unhandled Telegram update error", exc_info=context.error)
