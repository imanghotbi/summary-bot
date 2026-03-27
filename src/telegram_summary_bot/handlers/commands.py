from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from telegram_summary_bot.infrastructure.llm.client import LLMError
from telegram_summary_bot.services.jalali import (
    JalaliDateParseError,
    format_jalali_datetime,
    parse_summary_range,
)
from telegram_summary_bot.services.summary import build_transcript
from telegram_summary_bot.services.telegram_context import get_services

LOGGER = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if message is None:
        return
    await message.reply_text(
        "این ربات پیام‌های گروه را تا ۷ روز نگه می‌دارد و با دستور /summary روی بازه زمانی جلالی، خلاصه فارسی می‌سازد."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if message is None:
        return
    await message.reply_text(
        "نمونه استفاده:\n"
        "/summary 1405-01-01 08:00 | 1405-01-01 18:00\n\n"
        "همچنین می‌توانید از `تا` هم استفاده کنید:\n"
        "/summary 1405/01/01 08:00 تا 1405/01/01 18:00"
    )


async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat
    if message is None or chat is None:
        return

    services = get_services(context)
    command_text = extract_command_body(message.text or "")
    try:
        start_at, end_at = parse_summary_range(command_text, services.settings.app_timezone)
    except JalaliDateParseError as exc:
        await message.reply_text(str(exc))
        return

    status_message = await message.reply_text("در حال تهیه خلاصه...")

    rows = await services.repository.fetch_messages_between(
        chat_id=chat.id,
        start_at=start_at,
        end_at=end_at,
        max_messages=services.settings.summary_max_messages,
    )
    if not rows:
        await status_message.edit_text("در این بازه زمانی پیامی ذخیره نشده است.")
        return

    transcript, truncated = build_transcript(
        rows=rows,
        timezone_name=services.settings.app_timezone,
        max_chars=services.settings.summary_max_input_chars,
    )

    try:
        summary = await services.llm_client.summarize(
            group_title=chat.title,
            start_at_jalali=format_jalali_datetime(start_at, services.settings.app_timezone),
            end_at_jalali=format_jalali_datetime(end_at, services.settings.app_timezone),
            transcript=transcript,
            truncated=truncated or len(rows) >= services.settings.summary_max_messages,
        )
    except LLMError:
        LOGGER.exception("LLM summarization failed.")
        await status_message.edit_text("خلاصه‌سازی انجام نشد. اتصال مدل یا پراکسی را بررسی کنید.")
        return
    except Exception:
        LOGGER.exception("Unexpected summarization failure.")
        await status_message.edit_text("خطای داخلی رخ داد. دوباره تلاش کنید.")
        return

    await status_message.edit_text(summary)


def extract_command_body(text: str) -> str:
    parts = text.split(maxsplit=1)
    if len(parts) == 1:
        return ""
    return parts[1].strip()
