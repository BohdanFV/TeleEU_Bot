from __future__ import annotations

import datetime as dt
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


PROJECT_DIR = Path(__file__).resolve().parents[2]

DEFAULT_LESSON_TYPE_KEYWORDS = {
    "zoom": ["л", "лекція", "ккр", "шк", "захист", "іспит", "шкзалік"],
    "meet": ["пр", "практична", "прзалік", "залік", "лаб"],
}


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    bot_username: str
    database_path: Path
    data_dir: Path
    logs_dir: Path
    google_api_key: str
    debug_chat_id: int | None
    debug_error_thread_id: int | None
    debug_critical_thread_id: int | None

    # Runtime mode
    test_mode: bool = False
    test_first_time: dt.datetime | None = None
    test_speed_time: int = 1
    test_update_request: bool = True

    # Schedule/course logic
    notify_before_minutes: int = 6
    test_notify_before_minutes: int = 5
    update_schedule_every_day: bool = False
    update_links_enabled: bool = True
    month_of_course_change: int = 7
    day_of_course_change: int = 1

    # Retry/polling behavior
    schedule_attempts: int = 3
    schedule_attempt_pause: int = 10
    notification_attempts: int = 5
    notification_attempt_pause: int = 10
    notification_retry_window_minutes: int = 5
    polling_timeout: int = 123
    polling_restart_pause: int = 10

    # URLs/data sources
    web_schedule_url: str = "https://shedulem.e-u.edu.ua/"
    access_codes_url: str = "https://docs.google.com/spreadsheets/d/12dLLtBPWLm7jv3z9lXbjqeOFoQH1f-v2FSDybib4IFo/edit?gid=0#gid=0"
    fallback_resources_url: str = "https://docs.google.com/spreadsheets/d/1a0kG9NY6e7-OreY7nxKmTqPREBTvzsdhq2N1QGvn6gE/edit#gid=0"
    links_source_url: str = "https://shedulem.e-u.edu.ua/config/links.json"
    faculties_source_url: str = "https://shedulem.e-u.edu.ua/config/faculties.json"
    google_sheets_api_base_url: str = "https://sheets.googleapis.com/v4/spreadsheets"

    # Parsing/link detection
    lesson_type_keywords: dict[str, list[str]] | None = None

    # Logging
    log_level: str = "INFO"



def _load_env() -> Path | None:
    """Load .env from the current project folder first, then from package root.

    Running from the project root, from src/, or after editable installation
    should all work on Windows PowerShell and Linux shells.
    """

    candidates = [
        Path.cwd() / ".env",
        Path.cwd().parent / ".env",
        PROJECT_DIR / ".env",
    ]

    seen: set[Path] = set()
    for env_path in candidates:
        env_path = env_path.resolve()
        if env_path in seen:
            continue
        seen.add(env_path)
        if env_path.exists():
            load_dotenv(env_path, override=True, encoding="utf-8-sig")
            return env_path

    load_dotenv(override=True, encoding="utf-8-sig")
    return None


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _int_env(name: str, default: int | None = None) -> int | None:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return int(value)


def _str_env(name: str, default: str = "") -> str:
    value = os.getenv(name)
    return default if value is None else value.strip()


def _path_from_value(raw_value: str | None, default: str | Path, base_dir: Path) -> Path:
    path = Path(raw_value) if raw_value else Path(default)
    if not path.is_absolute():
        path = base_dir / path
    return path.expanduser().resolve()


def _path_env(name: str, default: str | Path, base_dir: Path) -> Path:
    return _path_from_value(os.getenv(name), default, base_dir)


def _datetime_env(name: str) -> dt.datetime | None:
    value = os.getenv(name)
    if not value or value.strip().lower() in {"now", "current", "datetime.now()"}:
        return None
    value = value.strip()
    for fmt in (None, "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%d.%m.%Y %H:%M:%S"):
        try:
            return dt.datetime.fromisoformat(value) if fmt is None else dt.datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(f"Invalid {name}. Use ISO format like 2026-02-10T08:44:50 or leave empty for current time.")


def _keywords_env(name: str) -> dict[str, list[str]]:
    value = os.getenv(name)
    if not value or not value.strip():
        return DEFAULT_LESSON_TYPE_KEYWORDS

    value = value.strip()
    try:
        parsed: Any = json.loads(value)
        if not isinstance(parsed, dict):
            raise ValueError
        result: dict[str, list[str]] = {}
        for key, items in parsed.items():
            if isinstance(items, str):
                result[str(key)] = [item.strip() for item in items.split(",") if item.strip()]
            elif isinstance(items, list):
                result[str(key)] = [str(item).strip() for item in items if str(item).strip()]
            else:
                raise ValueError
        return result
    except Exception as exc:
        raise ValueError(f"Invalid {name}. Use JSON, for example: {{\"zoom\":[\"л\"],\"meet\":[\"пр\"]}}") from exc


def load_settings() -> Settings:
    """Load application settings from .env/environment variables."""

    env_path = _load_env()
    base_dir = env_path.parent if env_path else PROJECT_DIR

    test_mode = _bool_env("TEST_MODE", False)
    token_var = "TEST_TELEGRAM_BOT_TOKEN" if test_mode else "TELEGRAM_BOT_TOKEN"
    username_var = "TEST_BOT_USERNAME" if test_mode else "BOT_USERNAME"

    default_db = "data/TeleEU_Bot_test.db" if test_mode else "data/TeleEU_Bot.db"
    db_value = os.getenv("TEST_DATABASE_PATH") if test_mode else os.getenv("DATABASE_PATH")
    # In test mode, keep test data isolated from the production database.
    if not db_value and not test_mode:
        db_value = os.getenv("DATABASE_PATH")

    telegram_bot_token = os.getenv(token_var) or os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not telegram_bot_token:
        checked = [str(Path.cwd() / ".env"), str(Path.cwd().parent / ".env"), str(PROJECT_DIR / ".env")]
        raise RuntimeError(
            "Telegram bot token is not configured. "
            f"Expected {token_var} or TELEGRAM_BOT_TOKEN in .env. "
            f"Checked: {', '.join(checked)}"
        )

    notify_before_default = _int_env("TEST_NOTIFY_BEFORE_MINUTES", 5) if test_mode else _int_env("NOTIFY_BEFORE_MINUTES", 6)

    return Settings(
        telegram_bot_token=telegram_bot_token,
        bot_username=os.getenv(username_var, os.getenv("BOT_USERNAME", "@EU_UA_Bot")),
        database_path=_path_from_value(db_value, default_db, base_dir),
        data_dir=_path_env("DATA_DIR", "data", base_dir),
        logs_dir=_path_env("LOGS_DIR", "logs", base_dir),
        google_api_key=os.getenv("GOOGLE_API_KEY", ""),
        debug_chat_id=_int_env("DEBUG_CHAT_ID"),
        debug_error_thread_id=_int_env("DEBUG_ERROR_THREAD_ID"),
        debug_critical_thread_id=_int_env("DEBUG_CRITICAL_THREAD_ID"),
        test_mode=test_mode,
        test_first_time=_datetime_env("TEST_FIRST_TIME"),
        test_speed_time=int(os.getenv("TEST_SPEED_TIME", "1")),
        test_update_request=_bool_env("TEST_UPDATE_REQUEST", True),
        notify_before_minutes=int(notify_before_default or 6),
        test_notify_before_minutes=int(_int_env("TEST_NOTIFY_BEFORE_MINUTES", 5) or 5),
        update_schedule_every_day=_bool_env("UPDATE_SCHEDULE_EVERY_DAY", False),
        update_links_enabled=_bool_env("UPDATE_LINKS_ENABLED", True),
        month_of_course_change=int(os.getenv("MONTH_OF_COURSE_CHANGE", "7")),
        day_of_course_change=int(os.getenv("DAY_OF_COURSE_CHANGE", "1")),
        schedule_attempts=int(os.getenv("SCHEDULE_ATTEMPTS", "3")),
        schedule_attempt_pause=int(os.getenv("SCHEDULE_ATTEMPT_PAUSE", "10")),
        notification_attempts=int(os.getenv("NOTIFICATION_ATTEMPTS", "5")),
        notification_attempt_pause=int(os.getenv("NOTIFICATION_ATTEMPT_PAUSE", "10")),
        notification_retry_window_minutes=int(os.getenv("NOTIFICATION_RETRY_WINDOW_MINUTES", "5")),
        polling_timeout=int(os.getenv("POLLING_TIMEOUT", "123")),
        polling_restart_pause=int(os.getenv("POLLING_RESTART_PAUSE", "10")),
        web_schedule_url=_str_env("WEB_SCHEDULE_URL", "https://shedulem.e-u.edu.ua/"),
        access_codes_url=_str_env("ACCESS_CODES_URL", Settings.access_codes_url),
        fallback_resources_url=_str_env("FALLBACK_RESOURCES_URL", Settings.fallback_resources_url),
        links_source_url=_str_env("LINKS_SOURCE_URL", "https://shedulem.e-u.edu.ua/config/links.json"),
        faculties_source_url=_str_env("FACULTIES_SOURCE_URL", "https://shedulem.e-u.edu.ua/config/faculties.json"),
        google_sheets_api_base_url=_str_env("GOOGLE_SHEETS_API_BASE_URL", "https://sheets.googleapis.com/v4/spreadsheets"),
        lesson_type_keywords=_keywords_env("LESSON_TYPE_KEYWORDS"),
        log_level=_str_env("LOG_LEVEL", "INFO").upper(),
    )
