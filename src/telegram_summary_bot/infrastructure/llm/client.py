from __future__ import annotations

from typing import Any

import httpx

from telegram_summary_bot.core.config import Settings
from telegram_summary_bot.infrastructure.llm.prompts import (
    SUMMARY_SYSTEM_PROMPT,
    build_summary_user_prompt,
)


class LLMError(RuntimeError):
    pass


class SummaryLLMClient:
    def __init__(self, settings: Settings) -> None:
        base_url = settings.llm_api_base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {settings.llm_api_key}",
                "Content-Type": "application/json",
            },
            timeout=settings.llm_request_timeout_seconds,
            proxy=settings.outbound_proxy_url,
        )
        self._model = settings.llm_model

    async def close(self) -> None:
        await self._client.aclose()

    async def summarize(
        self,
        *,
        group_title: str | None,
        start_at_jalali: str,
        end_at_jalali: str,
        transcript: str,
        truncated: bool,
    ) -> str:
        payload = {
            "model": self._model,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": build_summary_user_prompt(
                        group_title=group_title,
                        start_at_jalali=start_at_jalali,
                        end_at_jalali=end_at_jalali,
                        transcript=transcript,
                        truncated=truncated,
                    ),
                },
            ],
        }
        response = await self._client.post("/chat/completions", json=payload)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise LLMError(
                f"LLM request failed with status {exc.response.status_code}: {exc.response.text}"
            ) from exc

        data: dict[str, Any] = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError("Unexpected LLM response payload.") from exc

        if isinstance(content, list):
            parts = [part.get("text", "") for part in content if isinstance(part, dict)]
            content = "\n".join(part for part in parts if part)

        if not isinstance(content, str) or not content.strip():
            raise LLMError("LLM returned an empty summary.")
        return content.strip()
