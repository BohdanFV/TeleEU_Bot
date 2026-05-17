from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"


def setup_logging(logs_dir: Path, log_level: str = "INFO") -> None:
    logs_dir.mkdir(parents=True, exist_ok=True)

    level = getattr(logging, log_level.upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()

    formatter = logging.Formatter(LOG_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    general_handler = RotatingFileHandler(
        logs_dir / "general.log", maxBytes=1_000_000, backupCount=5, encoding="utf-8"
    )
    general_handler.setLevel(level)
    general_handler.setFormatter(formatter)
    root.addHandler(general_handler)

    error_handler = RotatingFileHandler(
        logs_dir / "errors.log", maxBytes=1_000_000, backupCount=5, encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root.addHandler(error_handler)
