from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import jdatetime


SUPPORTED_FORMATS = (
    "%Y-%m-%d %H:%M",
    "%Y/%m/%d %H:%M",
    "%Y-%m-%d",
    "%Y/%m/%d",
)
RELATIVE_RANGE_RE = re.compile(r"^(?P<value>\d{1,3})\s*(?P<unit>[mh])$", re.IGNORECASE)


class JalaliDateParseError(ValueError):
    pass


def get_timezone(timezone_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise JalaliDateParseError(
            f"منطقه زمانی `{timezone_name}` در سیستم در دسترس نیست. اگر روی ویندوز هستید، `uv sync` را اجرا کنید تا بسته tzdata نصب شود."
        ) from exc


def parse_jalali_datetime(value: str, timezone_name: str, *, end_of_day: bool = False) -> datetime:
    cleaned = " ".join(value.strip().split())
    timezone = get_timezone(timezone_name)
    for date_format in SUPPORTED_FORMATS:
        try:
            jalali_dt = jdatetime.datetime.strptime(cleaned, date_format)
            gregorian = jalali_dt.togregorian()
            local_dt = gregorian.replace(tzinfo=timezone)
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
    localized = value.astimezone(get_timezone(timezone_name))
    jalali_dt = jdatetime.datetime.fromgregorian(datetime=localized.replace(tzinfo=None))
    return jalali_dt.strftime("%Y-%m-%d %H:%M")


def parse_summary_range(text: str, timezone_name: str) -> tuple[datetime, datetime]:
    body = text.strip()
    if not body:
        raise JalaliDateParseError(
            "بازه زمانی را بعد از دستور وارد کنید. نمونه: /summary today یا /summary 1405-01-01 08:00 | 1405-01-01 18:00"
        )

    shortcut_range = parse_shortcut_range(body, timezone_name)
    if shortcut_range is not None:
        return shortcut_range

    separators = ("|", " تا ", "\n", " to ")
    parts: list[str] | None = None
    for separator in separators:
        if separator in body:
            parts = [part.strip() for part in body.split(separator, maxsplit=1)]
            break

    if not parts or len(parts) != 2 or not all(parts):
        raise JalaliDateParseError(
            "بازه زمانی را با `|` یا `تا` جدا کنید، یا از میانبرهایی مثل today، yesterday، week، 2h، 30m استفاده کنید."
        )

    start_at = parse_jalali_datetime(parts[0], timezone_name)
    end_at = parse_jalali_datetime(parts[1], timezone_name, end_of_day=True)
    if end_at <= start_at:
        raise JalaliDateParseError("زمان پایان باید بعد از زمان شروع باشد.")
    return start_at, end_at


def parse_shortcut_range(text: str, timezone_name: str) -> tuple[datetime, datetime] | None:
    normalized = " ".join(text.strip().lower().split())
    timezone = get_timezone(timezone_name)
    now_local = datetime.now(timezone)

    if normalized in {"today", "امروز"}:
        start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        return start_local.astimezone(UTC), now_local.astimezone(UTC)

    if normalized in {"yesterday", "دیروز"}:
        yesterday = now_local - timedelta(days=1)
        start_local = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_local = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        return start_local.astimezone(UTC), end_local.astimezone(UTC)

    if normalized in {"week", "thisweek", "this_week", "هفته", "این هفته"}:
        start_local = (now_local - timedelta(days=now_local.weekday())).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        return start_local.astimezone(UTC), now_local.astimezone(UTC)

    match = RELATIVE_RANGE_RE.fullmatch(normalized)
    if match is None:
        return None

    value = int(match.group("value"))
    unit = match.group("unit").lower()
    if value <= 0:
        raise JalaliDateParseError("بازه نسبی باید بزرگ‌تر از صفر باشد.")

    if unit == "h":
        delta = timedelta(hours=value)
    else:
        delta = timedelta(minutes=value)

    start_local = now_local - delta
    return start_local.astimezone(UTC), now_local.astimezone(UTC)
