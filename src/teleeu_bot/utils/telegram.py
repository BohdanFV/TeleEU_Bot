from __future__ import annotations


def get_message_id(message) -> int | None:
    """Return message id for pyTelegramBotAPI objects across versions."""

    return getattr(message, "message_id", getattr(message, "id", None))
