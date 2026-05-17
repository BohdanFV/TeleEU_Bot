from __future__ import annotations

import datetime as dt
import logging

import telebot

from .registration import send_not_registered

logger = logging.getLogger(__name__)


def send_access_codes(app, message) -> None:
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("Відкрити", url=app.settings.access_codes_url))
    app.bot.send_message(message.chat.id, "Коди доступу до навчальних ресурсів ЄУ", reply_markup=markup, disable_notification=True)


def send_schedule(app, message, now: dt.datetime, days: list[dt.datetime], include_links: bool = False) -> None:
    entries, missing = app.schedule_service.get_user_schedule(message.chat.id, now)
    if not entries and not app.db.is_registered(message.chat.id):
        send_not_registered(app, message)
        return

    if missing:
        groups = ", ".join(missing)
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            telebot.types.InlineKeyboardButton("✏ Перереєструватися", callback_data="reregist"),
            telebot.types.InlineKeyboardButton("Повідомити про помилку", callback_data=f"err_{message.chat.id}_to send schedule for group(s) {groups}"),
        )
        app.bot.send_message(
            message.chat.id,
            f"Розклад для груп {groups} не знайдено. Можливо, групу вказано неправильно.",
            reply_markup=markup,
            disable_notification=True,
        )

    links_data = app.link_service.load() if include_links else {}
    messages = app.schedule_service.format_messages(entries, days, links_data=links_data, now=app.now())
    if not messages:
        app.bot.send_message(message.chat.id, "Немає розкладу :(", disable_notification=True)
        return

    for text in messages:
        app.bot.send_message(
            message.chat.id,
            text,
            parse_mode="HTML",
            disable_notification=True,
            disable_web_page_preview=True,
        )


def send_next_lessons(app, chat_id: int, shift: int = 0) -> None:
    try:
        now = app.now()
        schedule_data = app.schedule_service.load_schedule(now)
        if not schedule_data:
            app.bot.send_message(chat_id, "Немає розкладу :(", disable_notification=True)
            return

        times = []
        for date_label, day_times in schedule_data.get("times", {}).items():
            for time_label in day_times:
                if not date_label or not time_label:
                    continue
                try:
                    candidate = dt.datetime.strptime(f"{date_label},{time_label},{now.year}", "%d.%m,%H:%M,%Y")
                except ValueError:
                    continue
                times.append(candidate)
        times = sorted(times)
        next_time = next((item for item in times if item > now), None)
        if next_time is None:
            raise ValueError("No next lesson")
        index = times.index(next_time) + shift
        if not (0 <= index < len(times)):
            raise ValueError("Shift is out of range")
        next_time = times[index]

        links_data = app.link_service.load()
        str_day = next_time.strftime("%d.%m")
        str_time = next_time.strftime("%H:%M")
        app.bot.send_message(chat_id, text=f"〰️     {next_time.strftime('%H:%M %d.%m')}     〰️", parse_mode="HTML", disable_notification=True)

        data = {"denna": {}, "zaochna": {}}
        for faculty_data in schedule_data.values():
            if not isinstance(faculty_data, dict):
                continue
            for edu_form in data:
                for group, group_data in faculty_data.get(edu_form, {}).items():
                    lesson = group_data.get(str_day, {}).get(str_time)
                    if not lesson:
                        continue
                    lesson_type = lesson.get("type", "")
                    subject = lesson.get("subject", "")
                    data[edu_form].setdefault(lesson_type, {}).setdefault(subject, []).append(group)

        for edu_form, lessons_by_type in data.items():
            app.bot.send_message(chat_id, text=f"\n<b>〰️〰️〰️ {edu_form} 〰️〰️〰️</b>", parse_mode="HTML", disable_notification=True)
            for lesson_type, lessons in lessons_by_type.items():
                text = f"<b>{lesson_type}  〰️〰️\n</b>"
                for lesson_subject, groups in lessons.items():
                    text += f"\n{lesson_subject.replace(chr(10), ' ')}\n{' '.join(groups)}\n"
                app.bot.send_message(chat_id, text=text, parse_mode="HTML", disable_notification=True, disable_web_page_preview=True)
    except Exception:
        logger.exception("Failed to send next lessons")
        app.bot.send_message(chat_id, text="Немає розкладу :(", parse_mode="HTML", disable_notification=True)
