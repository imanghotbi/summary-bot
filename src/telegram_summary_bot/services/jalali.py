from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import jdatetime


SUPPORTED_FORMATS = (
    "%Y-%m-%d %H:%M",
    "%Y/%m/%d %H:%M",
    "%Y-%m-%d",
    "%Y/%m/%d",
)


class JalaliDateParseError(ValueError):
    pass


def parse_jalali_datetime(value: str, timezone_name: str, *, end_of_day: bool = False) -> datetime:
    cleaned = " ".join(value.strip().split())
    for date_format in SUPPORTED_FORMATS:
        try:
            jalali_dt = jdatetime.datetime.strptime(cleaned, date_format)
            gregorian = jalali_dt.togregorian()
            local_dt = gregorian.replace(tzinfo=ZoneInfo(timezone_name))
            if "%H" not in date_format:
                if end_of_day:
                    local_dt = local_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
                else:
                    local_dt = local_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            return local_dt.astimezone(UTC)
        except ValueError:
            continue
    raise JalaliDateParseError(
        "فرمت تاریخ نامعتبر است. نمونه درست: 1405-01-01 08:00"
    )


def format_jalali_datetime(value: datetime, timezone_name: str) -> str:
    localized = value.astimezone(ZoneInfo(timezone_name))
    jalali_dt = jdatetime.datetime.fromgregorian(datetime=localized.replace(tzinfo=None))
    return jalali_dt.strftime("%Y-%m-%d %H:%M")


def parse_summary_range(text: str, timezone_name: str) -> tuple[datetime, datetime]:
    body = text.strip()
    if not body:
        raise JalaliDateParseError(
            "بازه زمانی را بعد از دستور وارد کنید. نمونه: /summary 1405-01-01 08:00 | 1405-01-01 18:00"
        )

    separators = ("|", " تا ", "\n", " to ")
    parts: list[str] | None = None
    for separator in separators:
        if separator in body:
            parts = [part.strip() for part in body.split(separator, maxsplit=1)]
            break

    if not parts or len(parts) != 2 or not all(parts):
        raise JalaliDateParseError(
            "بازه زمانی را با `|` یا `تا` جدا کنید. نمونه: 1405-01-01 08:00 | 1405-01-01 18:00"
        )

    start_at = parse_jalali_datetime(parts[0], timezone_name)
    end_at = parse_jalali_datetime(parts[1], timezone_name, end_of_day=True)
    if end_at <= start_at:
        raise JalaliDateParseError("زمان پایان باید بعد از زمان شروع باشد.")
    return start_at, end_at
