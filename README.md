# Telegram Summary Bot

Async Telegram bot for group chats. It stores group messages in SQLite for 7 days, accepts a Jalali date-time range, sends the selected messages to an OpenAI-compatible language model through a proxy, and posts a Persian summary back to the group.

## Features

- Async Telegram handlers based on `python-telegram-bot`
- Async SQLAlchemy + SQLite storage
- 7-day retention with background cleanup
- Jalali date/time parsing for summary requests
- Persian summaries with sender names
- OpenAI-compatible LLM API over HTTP proxy
- Env configuration via `pydantic-settings`

## Project Structure

```text
src/telegram_summary_bot/
  bootstrap/       # App assembly and handler registration
  core/            # Settings, logging, shared app types
  handlers/        # Telegram command/message/error handlers
  infrastructure/  # Database, LLM client, app lifecycle
  services/        # Jalali parsing, transcript building, context helpers
  main.py          # Process entrypoint
```

## Setup

```bash
uv sync
cp .env.example .env
```

Fill in `.env` with:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_BASE_URL` if you are using a Telegram-compatible social network
- `TELEGRAM_BASE_FILE_URL` if file endpoints are also served from a custom base
- `LLM_API_KEY`
- `LLM_MODEL`
- `LLM_API_BASE_URL`
- `OUTBOUND_PROXY_URL` if your LLM traffic must go through a proxy

## Run

```bash
uv run telegram-summary-bot
```

## Telegram Usage

Add the bot to a group and disable privacy mode if you want it to receive all group messages.

Commands:

- `/start`
- `/help`
- `/summary 1405-01-01 08:00 | 1405-01-01 18:00`
- `/summary 1405/01/01 08:00 تا 1405/01/01 18:00`

The bot will reply to the command message with a temporary status message such as "در حال تهیه خلاصه..." and then edit that message with the final Persian summary.

## Notes

- Times are interpreted in `APP_TIMEZONE`, default `Asia/Tehran`.
- Messages older than `RETENTION_DAYS` are deleted automatically.
- By default only text and caption-bearing messages are stored.
- For Telegram-compatible servers, keep the bot API base shaped like `https://host/.../bot` and files like `https://host/.../file/bot`.
