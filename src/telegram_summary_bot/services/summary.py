from __future__ import annotations

from telegram_summary_bot.infrastructure.db.models import StoredMessage
from telegram_summary_bot.services.jalali import format_jalali_datetime


def build_transcript(
    *,
    rows: list[StoredMessage],
    timezone_name: str,
    max_chars: int,
) -> tuple[str, bool]:
    lines: list[str] = []
    total_chars = 0
    truncated = False

    for row in rows:
        timestamp = format_jalali_datetime(row.created_at, timezone_name)
        line = f"[{timestamp}] {row.sender_name}: {row.text.strip()}"
        remaining = max_chars - total_chars
        if remaining <= 0:
            truncated = True
            break
        if len(line) > remaining:
            line = line[: max(0, remaining - 1)].rstrip() + "…"
            truncated = True
        lines.append(line)
        total_chars += len(line) + 1
        if truncated:
            break

    return "\n".join(lines), truncated
