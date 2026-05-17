from __future__ import annotations

import datetime as dt
import logging

import telebot

from . import admin, registration, schedule, settings

logger = logging.getLogger(__name__)


def register_command_handlers(app) -> None:
    @app.bot.message_handler(func=lambda message: True)
    def handle_message(message) -> None:
        text = message.text or ""
        logger.info("Message from %s: %s", message.chat.id, text)
        command = text.replace(app.settings.bot_username, "")
        now = app.now()

        if command == "/start":
            registration.register_user_flow(app, message)
        elif command == "/bot_on":
            settings.set_bot_mode(app, 1, message)
        elif command == "/bot_off":
            settings.set_bot_mode(app, 0, message)
        elif command == "/add_keyboard":
            app.bot.send_message(
                chat_id=message.chat.id,
                text="Оберіть клавіатуру яку хочете додати:\n👉/add_keyboard_1\n👉/add_keyboard_2",
                disable_notification=True,
            )
        elif command == "/add_keyboard_1":
            app.bot.send_message(
                chat_id=message.chat.id,
                text="Клавіатуру 1 додано! Для видалення клавіатури відправте /remove_keyboard",
                reply_markup=app.reply_keyboards[0],
                disable_notification=True,
            )
        elif command == "/add_keyboard_2":
            app.bot.send_message(
                chat_id=message.chat.id,
                text="Клавіатуру 2 додано! Для видалення клавіатури відправте /remove_keyboard",
                reply_markup=app.reply_keyboards[1],
                disable_notification=True,
            )
        elif command == "/remove_keyboard":
            app.bot.send_message(
                message.chat.id,
                "Клавіатуру приховано. Для відновлення відправте /add_keyboard",
                reply_markup=telebot.types.ReplyKeyboardRemove(),
                disable_notification=True,
            )
        elif command == "/ping":
            app.bot.send_message(message.chat.id, str(now), disable_notification=True)
        elif command == "/status":
            admin.send_status(app, message)
        elif command == "/Коди доступу":
            schedule.send_access_codes(app, message)
        elif command in {"/settings", "/Налаштування"}:
            settings.show_settings(app, message)
        elif command in {"/schedule_for_week", "/Розклад на цей тиждень"}:
            schedule.send_schedule(app, message, now, app.schedule_service.week_days(now), include_links=False)
        elif command in {"/schedule_for_today", "/Розклад на сьогодні"}:
            schedule.send_schedule(app, message, now, [now], include_links=True)
        elif command in {"/schedule_for_tomorrow", "/Розклад на завтра"}:
            tomorrow = now + dt.timedelta(days=1)
            schedule.send_schedule(app, message, tomorrow, [tomorrow], include_links=False)
        elif command.startswith("/next_lessons"):
            suffix = command[13:]
            schedule.send_next_lessons(app, message.chat.id, int(suffix) if suffix.isdigit() else 0)
        elif message.chat.id in app.registration:
            registration.continue_registration(app, message)
        elif command in {"/log_file", "Файл з Логами"}:
            admin.send_log_file(app, message.chat.id)
        elif command in {"/keyboard", "/k"}:
            app.bot.send_message(chat_id=message.chat.id, text="======= Клавіатура =======", reply_markup=app.inline_keyboard, disable_notification=True)
        elif command in {"/Розклад на тиждень"}:
            app.bot.send_message(chat_id=message.chat.id, text="Клавіатуру оновлено! Натисніть ще раз.", reply_markup=app.reply_keyboards[0], disable_notification=True)
        elif command.startswith("/"):
            app.bot.send_message(chat_id=message.chat.id, text="======= Клавіатура =======", reply_markup=app.inline_keyboard, disable_notification=True)
