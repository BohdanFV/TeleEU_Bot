from __future__ import annotations

import datetime as dt
import logging

import telebot

from . import registration, schedule, settings
from ..utils.telegram import get_message_id

logger = logging.getLogger(__name__)


def register_callback_handlers(app) -> None:
    @app.bot.callback_query_handler(func=lambda call: True)
    def handle_buttons(call) -> None:
        data = call.data or ""
        logger.info("Callback from %s: %s", call.message.chat.id, data)
        now = app.now()

        if data == "info":
            registration.show_info(app, call.message)
        elif data == "regist":
            registration.start_registration(app, call.message)
        elif data == "reregist":
            registration.unregister(app, call.message.chat.id)
            registration.start_registration(app, call.message)
        elif data.startswith("reg_fac="):
            registration.select_faculty(app, call)
        elif data in {"denna", "zaochna"}:
            registration.select_education_form(app, call)
        elif data == "turn_off":
            settings.set_bot_mode(app, 0, call.message)
        elif data == "turn_on":
            settings.set_bot_mode(app, 1, call.message)
        elif data == "settings":
            settings.show_settings(app, call.message, edit_message=True)
        elif data in {"reg_send_lesson_mode_0", "reg_send_lesson_mode_1"}:
            registration.finish_registration(app, call)
        elif data == "remove_keyboard":
            app.bot.send_message(
                call.message.chat.id,
                "Клавіатуру приховано. Для відновлення клавіатури відправте /add_keyboard",
                reply_markup=telebot.types.ReplyKeyboardRemove(),
                disable_notification=True,
            )
        elif data == "notification_settings":
            settings.show_notification_settings(app, call.message)
        elif data.startswith("chenge_data"):
            _, column_name, value = data.split("/", 2)
            settings.change_user_data(app, call.message.chat.id, column_name, value)
            settings.show_notification_settings(app, call.message)
        elif data.startswith("list_of_groups"):
            registration.show_groups_list(app, call)
        elif data == "access_codes":
            schedule.send_access_codes(app, call.message)
        elif data == "schedule_for_week":
            schedule.send_schedule(app, call.message, now, app.schedule_service.week_days(now), include_links=False)
        elif data == "schedule_for_today":
            schedule.send_schedule(app, call.message, now, [now], include_links=True)
        elif data == "schedule_for_tomorrow":
            tomorrow = now + dt.timedelta(days=1)
            schedule.send_schedule(app, call.message, tomorrow, [tomorrow], include_links=False)
        elif data.startswith("err"):
            logger.error("User error report: %s", data)
            app.send_debug_message(f"User error report: {data}", level="error")
            app.bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=get_message_id(call.message),
                text="Повідомлення про помилку надіслано розробнику.\nДякуємо за відгук!",
            )
