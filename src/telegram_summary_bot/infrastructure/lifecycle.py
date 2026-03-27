from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from telegram.ext import Application

from telegram_summary_bot.core.types import AppServices
from telegram_summary_bot.infrastructure.db.engine import (
    create_engine,
    create_session_factory,
    dispose_engine,
    init_database,
)
from telegram_summary_bot.infrastructure.db.repository import MessageRepository
from telegram_summary_bot.infrastructure.llm.client import SummaryLLMClient

LOGGER = logging.getLogger(__name__)


async def post_init(application: Application) -> None:
    settings = application.bot_data["settings"]
    settings.ensure_data_dir()

    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    await init_database(engine)

    services = AppServices(
        settings=settings,
        repository=MessageRepository(session_factory),
        llm_client=SummaryLLMClient(settings),
    )
    services.cleanup_task = asyncio.create_task(run_cleanup_loop(services), name="cleanup-loop")

    application.bot_data["engine"] = engine
    application.bot_data["services"] = services
    LOGGER.info("Application initialized.")


async def post_shutdown(application: Application) -> None:
    services: AppServices | None = application.bot_data.get("services")
    if services is not None:
        if services.cleanup_task is not None:
            services.cleanup_task.cancel()
            await asyncio.gather(services.cleanup_task, return_exceptions=True)
        await services.llm_client.close()

    engine = application.bot_data.get("engine")
    if engine is not None:
        await dispose_engine(engine)
    LOGGER.info("Application shutdown complete.")


async def run_cleanup_loop(services: AppServices) -> None:
    while True:
        try:
            cutoff = datetime.now(UTC) - timedelta(days=services.settings.retention_days)
            deleted = await services.repository.delete_older_than(cutoff=cutoff)
            if deleted:
                LOGGER.info("Deleted %s expired messages.", deleted)
        except asyncio.CancelledError:
            raise
        except Exception:
            LOGGER.exception("Cleanup loop failed.")
        await asyncio.sleep(services.settings.cleanup_interval_seconds)
