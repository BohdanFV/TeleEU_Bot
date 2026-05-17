from __future__ import annotations

import datetime as dt
import json
import logging

import telebot

from ..keyboards import not_registered_keyboard
from ..utils.dates import admission_year_from_course
from ..utils.parsing import parse_user_group
from ..utils.telegram import get_message_id

logger = logging.getLogger(__name__)


def register_user_flow(app, message) -> None:
    if app.db.is_registered(message.chat.id):
        app.bot.send_message(message.chat.id, "Ви вже зареєстровані!", disable_notification=True)
        return

    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("Зареєструватись", callback_data="regist"),
        telebot.types.InlineKeyboardButton("Про бот", callback_data="info"),
    )
    first_name = getattr(message.from_user, "first_name", "") or ""
    app.bot.send_message(
        message.chat.id,
        f"👋 Вітаю, {first_name}! Щоб скористатись ботом, вам потрібно зареєструватися.",
        reply_markup=markup,
        disable_notification=True,
    )


def show_info(app, message) -> None:
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("Зареєструватись", callback_data="regist"))
    app.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=get_message_id(message),
        text=(
            "Ласкаво просимо до бота для автоматизації розкладу Європейського Університету! "
            "Бот надсилає нагадування про заняття та допомагає швидко отримувати розклад.\n\n"
            "З повагою,\nРозробник: Фесенко Богдан"
        ),
        reply_markup=markup,
    )


def start_registration(app, message) -> None:
    faculties = app.schedule_service.load_faculties()
    markup = telebot.types.InlineKeyboardMarkup()
    for faculty in faculties:
        markup.add(telebot.types.InlineKeyboardButton(faculty["name"], callback_data=f"reg_fac={faculty['id']}"))
    app.bot.edit_message_text(chat_id=message.chat.id, message_id=get_message_id(message), text="Оберіть факультет:", reply_markup=markup)


def select_faculty(app, call) -> None:
    app.registration[call.message.chat.id] = {"faculty": call.data.replace("reg_fac=", "", 1)}
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("Денна", callback_data="denna"),
        telebot.types.InlineKeyboardButton("Заочна", callback_data="zaochna"),
        telebot.types.InlineKeyboardButton("🔙", callback_data="regist"),
    )
    app.bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=get_message_id(call.message),
        text="Оберіть вашу форму навчання:",
        reply_markup=markup,
    )


def select_education_form(app, call) -> None:
    chat_id = call.message.chat.id
    if chat_id not in app.registration:
        start_registration(app, call.message)
        return

    edu_form = call.data
    app.registration[chat_id]["edu_form"] = edu_form

    text = "<b>Введіть групу</b>"
    if chat_id < 0:
        text += " (у відповідь на це повідомлення)"
    text += (
        ":\nПерші три цифри — це факультет, група, підгрупа відповідно (<code>123/4_on</code>)\n"
        "Потім підгрупа (<code>123/4_on</code>)\n"
        "Після цього тип навчання (<code>123/4_on</code>): <code>on</code> — online, <code>of</code> — offline.\n"
        "Приклад: <code>123</code>, <code>123/4</code>, <code>123_of</code> або <code>123/4_on</code>\n\n"
        "Або оберіть групу із списку ⤵"
    )

    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton(
            "Обрати із списку",
            callback_data=f"list_of_groups/{app.registration[chat_id]['faculty']}/{edu_form}",
        ),
        telebot.types.InlineKeyboardButton("🔙", callback_data="regist"),
    )
    app.bot.edit_message_text(
        chat_id=chat_id,
        message_id=get_message_id(call.message),
        reply_markup=markup,
        text=text,
        parse_mode="HTML",
    )


def continue_registration(app, message) -> None:
    if message.chat.id not in app.registration:
        register_user_flow(app, message)
        return
    select_group(app, message)


def select_group(app, message) -> None:
    group_raw = message.text.replace(app.settings.bot_username, "")
    parsed = parse_user_group(group_raw)
    if not parsed:
        app.bot.send_message(
            message.chat.id,
            "Помилка формату введення. Введіть назву групи за зразком 123, 123/1, 123_of або 123/23_on.",
            disable_notification=True,
        )
        return

    faculty_num, course_num, subgroup = parsed
    app.registration[message.chat.id]["user_group"] = (faculty_num, course_num, subgroup)

    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton("Тільки про пари", callback_data="reg_send_lesson_mode_0"),
        telebot.types.InlineKeyboardButton("Про всі заняття", callback_data="reg_send_lesson_mode_1"),
        telebot.types.InlineKeyboardButton("🔙", callback_data="regist"),
    )
    app.bot.send_message(message.chat.id, "Які бажаєте отримувати повідомлення:", reply_markup=markup, disable_notification=True)


def finish_registration(app, call) -> None:
    chat_id = call.message.chat.id
    state = app.registration.get(chat_id)
    if not state or "user_group" not in state or "edu_form" not in state:
        register_user_flow(app, call.message)
        return

    now = app.now()
    faculty_num, course_num, subgroup = state["user_group"]
    admission_year = admission_year_from_course(
        now,
        course_num,
        app.settings.month_of_course_change,
        app.settings.day_of_course_change,
    )
    send_lesson_mode = int(call.data[-1])

    app.db.create_profile(
        chat_id=chat_id,
        first_name=call.message.chat.first_name,
        last_name=call.message.chat.last_name,
        username=call.message.chat.username,
        faculty=state["faculty"],
        edu_form=state["edu_form"],
        faculty_num=faculty_num,
        admission_year=admission_year,
        subgroup_num=subgroup,
        send_lesson_mode=send_lesson_mode,
    )

    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(telebot.types.InlineKeyboardButton("Вимкнути сповіщення", callback_data="turn_off"))
    app.bot.delete_message(chat_id=chat_id, message_id=get_message_id(call.message))
    group_name = f"{faculty_num}{course_num}{subgroup}"
    app.bot.send_message(
        chat_id=chat_id,
        text=(
            "<b>Вас зареєстровано!</b>\n"
            "〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️\n"
            f"Факультет - {state['faculty']}\n"
            f"Форма навчання - {state['edu_form']}\n"
            f"Група - {group_name}\n"
            "<i>*Дані можна змінити в налаштуваннях</i>"
        ),
        parse_mode="HTML",
        reply_markup=None if chat_id < 0 else app.reply_keyboards[1],
        disable_notification=True,
    )
    app.bot.send_message(chat_id, "Сповіщення про пару увімкнено!", reply_markup=markup, disable_notification=True)
    app.registration.pop(chat_id, None)
    logger.info("New user registered: user_id=%s", chat_id)


def unregister(app, chat_id: int) -> None:
    app.db.delete_profiles(chat_id)
    app.registration.pop(chat_id, None)


def show_groups_list(app, call) -> None:
    try:
        _, faculty, edu_form = call.data.split("/", 2)
        now = app.now()
        schedule_data = app.schedule_service.load_schedule(now) or {}
        groups = sorted(schedule_data.get(faculty, {}).get(edu_form, {}).keys())
        text = " /" + " /".join(groups) if groups else "👀 Наразі для вашого факультету розклад не знайдено."
    except Exception:
        logger.exception("Failed to show groups list")
        text = "Вибачте, сталася помилка в отриманні груп :("
    app.bot.send_message(call.message.chat.id, text, disable_notification=True)


def send_not_registered(app, message) -> None:
    app.bot.send_message(
        message.chat.id,
        "Схоже, ви не зареєстровані в системі. Зареєструйтесь для початку роботи.",
        reply_markup=not_registered_keyboard(),
        disable_notification=True,
    )
