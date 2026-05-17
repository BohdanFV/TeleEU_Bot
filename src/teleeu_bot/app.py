from __future__ import annotations

import datetime as dt
import logging
import threading
import time

import requests
import telebot

from .config import Settings, load_settings
from .database import Database
from .keyboards import main_inline_keyboard, reply_keyboards
from .logging_config import setup_logging
from .services.links import LinkService
from .services.notifications import NotificationService
from .services.schedules import ScheduleService
from .utils.dates import AcceleratedDateTime

logger = logging.getLogger(__name__)


class TeleEUBotApplication:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        setup_logging(settings.logs_dir, settings.log_level)

        self.bot = telebot.TeleBot(settings.telegram_bot_token)
        self.db = Database(settings.database_path)
        self.link_service = LinkService(settings)
        self.schedule_service = ScheduleService(settings, self.db, self.link_service)
        self.notification_service = NotificationService(self)

        self.reply_keyboards = reply_keyboards(settings.web_schedule_url)
        self.inline_keyboard = main_inline_keyboard(settings.web_schedule_url)
        self.registration: dict[int, dict[str, object]] = {}

        self.clock = None
        if settings.test_mode:
            self.clock = AcceleratedDateTime(settings.test_first_time or dt.datetime.now(), settings.test_speed_time)

        self.polling_thread: threading.Thread | None = None
        self.notification_thread: threading.Thread | None = None

    def real_now(self) -> dt.datetime:
        return dt.datetime.now()

    def now(self) -> dt.datetime:
        if self.clock:
            return self.clock.now()
        return self.real_now()

    def register_handlers(self) -> None:
        from .handlers.callbacks import register_callback_handlers
        from .handlers.commands import register_command_handlers

        register_command_handlers(self)
        register_callback_handlers(self)

    def send_debug_message(self, text: str, level: str = "info") -> None:
        if not self.settings.debug_chat_id:
            return
        try:
            kwargs = {"chat_id": self.settings.debug_chat_id, "text": text}
            if level == "error" and self.settings.debug_error_thread_id:
                kwargs["message_thread_id"] = self.settings.debug_error_thread_id
            if level == "critical" and self.settings.debug_critical_thread_id:
                kwargs["message_thread_id"] = self.settings.debug_critical_thread_id
            self.bot.send_message(**kwargs)
        except Exception:
            logger.exception("Failed to send debug message")

    def run_polling(self) -> None:
        if self.settings.test_mode:
            self.bot.polling(none_stop=True, timeout=self.settings.polling_timeout)
            return

        while True:
            try:
                self.bot.polling(none_stop=True, timeout=self.settings.polling_timeout)
            except ConnectionResetError:
                logger.exception("Connection reset")
            except requests.exceptions.ReadTimeout:
                logger.exception("Read timeout")
            except requests.exceptions.RequestException:
                logger.exception("HTTP error")
            except Exception:
                logger.exception("Bot polling crashed")
            logger.info("Restart polling in %s seconds", self.settings.polling_restart_pause)
            time.sleep(self.settings.polling_restart_pause)

    def start(self) -> None:
        self.db.init_schema()
        self.register_handlers()
        self.link_service.update()
        logger.info("Bot started")
        self.send_debug_message(f"{self.now()} [INFO] - Bot started")

        self.polling_thread = threading.Thread(target=self.run_polling, name="bot-polling", daemon=True)
        self.notification_thread = threading.Thread(target=self.notification_service.run_forever, name="notifications", daemon=True)
        self.polling_thread.start()
        self.notification_thread.start()
        self.polling_thread.join()
        self.notification_thread.join()


def main() -> None:
    app = TeleEUBotApplication(load_settings())
    app.start()
