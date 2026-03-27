from __future__ import annotations

import asyncio
from dataclasses import dataclass

from telegram_summary_bot.core.config import Settings
from telegram_summary_bot.infrastructure.db.repository import MessageRepository
from telegram_summary_bot.infrastructure.llm.client import SummaryLLMClient


@dataclass(slots=True)
class AppServices:
    settings: Settings
    repository: MessageRepository
    llm_client: SummaryLLMClient
    cleanup_task: asyncio.Task[None] | None = None
