from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from telegram_summary_bot.infrastructure.db.models import StoredMessage


class MessageRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def save_message(
        self,
        *,
        chat_id: int,
        chat_title: str | None,
        message_id: int,
        sender_user_id: int | None,
        sender_name: str,
        text: str,
        created_at: datetime,
    ) -> None:
        async with self._session_factory() as session:
            session.add(
                StoredMessage(
                    chat_id=chat_id,
                    chat_title=chat_title,
                    message_id=message_id,
                    sender_user_id=sender_user_id,
                    sender_name=sender_name,
                    text=text,
                    created_at=created_at,
                )
            )
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()

    async def fetch_messages_between(
        self,
        *,
        chat_id: int,
        start_at: datetime,
        end_at: datetime,
        max_messages: int,
    ) -> list[StoredMessage]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(StoredMessage)
                .where(
                    StoredMessage.chat_id == chat_id,
                    StoredMessage.created_at >= start_at,
                    StoredMessage.created_at <= end_at,
                )
                .order_by(StoredMessage.created_at.asc(), StoredMessage.id.asc())
                .limit(max_messages)
            )
            return list(result.scalars().all())

    async def delete_older_than(self, *, cutoff: datetime) -> int:
        async with self._session_factory() as session:
            result = await session.execute(
                delete(StoredMessage).where(StoredMessage.created_at < cutoff)
            )
            await session.commit()
            return int(result.rowcount or 0)
