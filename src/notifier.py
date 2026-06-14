"""Send messages to Telegram via the Bot API."""

from __future__ import annotations

import logging

import requests

logger = logging.getLogger(__name__)

MAX_LENGTH = 4096
API_TIMEOUT = 15  # seconds


def send(token: str, chat_id: str, text: str) -> None:
    """POST a message to Telegram, truncating to the 4096-char limit."""
    if len(text) > MAX_LENGTH:
        text = text[: MAX_LENGTH - 3] + "..."

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        resp = requests.post(
            url,
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            timeout=API_TIMEOUT,
        )
        resp.raise_for_status()
    except requests.HTTPError as exc:
        body = exc.response.text if exc.response is not None else ""
        logger.error("Telegram send failed (chat %s): %s — %s", chat_id, exc, body)
    except requests.RequestException as exc:
        logger.error("Telegram send failed (chat %s): %s", chat_id, exc)


def format_message(description: str, output: str) -> str:
    return f"*{description}*\n\n```\n{output}\n```"
