from __future__ import annotations

import logging
from datetime import UTC

from telegram import Message, Update
from telegram.constants import ChatType
from telegram.ext import ContextTypes

from telegram_summary_bot.services.telegram_context import get_services

LOGGER = logging.getLogger(__name__)


async def store_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat
    if message is None or chat is None or chat.type not in {ChatType.GROUP, ChatType.SUPERGROUP}:
        return

    if message.from_user and message.from_user.is_bot:
        return

    text = extract_message_text(message)
    if not text or text.startswith("/"):
        return

    services = get_services(context)
    sender = message.from_user
    sender_name = sender.full_name if sender else "Unknown"
    created_at = message.date.astimezone(UTC)

    try:
        await services.repository.save_message(
            chat_id=chat.id,
            chat_title=chat.title,
            message_id=message.message_id,
            sender_user_id=sender.id if sender else None,
            sender_name=sender_name,
            text=text,
            created_at=created_at,
        )
    except Exception:
        LOGGER.exception(
            "Failed to store message for chat_id=%s message_id=%s",
            chat.id,
            message.message_id,
        )


def extract_message_text(message: Message) -> str | None:
    if message.text:
        return message.text.strip()
    if message.caption:
        return message.caption.strip()
    return None
