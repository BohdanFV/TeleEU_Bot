from __future__ import annotations

import telebot

from ..utils.dates import build_group_name
from ..utils.telegram import get_message_id
from .registration import send_not_registered


def show_settings(app, message, edit_message: bool = False) -> None:
    profiles = app.db.get_profiles(message.chat.id)
    if not profiles:
        send_not_registered(app, message)
        return

    now = app.now()
    text = "<b>Налаштування:</b>\n〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️"
    for profile in profiles:
        group = build_group_name(now, profile.faculty_num, profile.admission_year, profile.subgroup_num)
        text += f"\nФакультет - {profile.faculty}"
        text += f"\nФорма навчання - {profile.edu_form}"
        text += f"\nГрупа - {group}"

    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton("Змінити інформацію", callback_data="reregist"),
        telebot.types.InlineKeyboardButton("Додати ще один акаунт", callback_data="regist"),
        telebot.types.InlineKeyboardButton("Налаштування повідомлень", callback_data="notification_settings"),
        telebot.types.InlineKeyboardButton("Прибрати клавіатуру", callback_data="remove_keyboard"),
    )
    if edit_message:
        app.bot.edit_message_text(chat_id=message.chat.id, message_id=get_message_id(message), text=text, reply_markup=markup, parse_mode="HTML")
    else:
        app.bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="HTML", disable_notification=True)


def show_notification_settings(app, message) -> None:
    user = app.db.get_notification_settings(message.chat.id)
    if not user:
        send_not_registered(app, message)
        return

    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    text = "<b>Налаштування повідомлень:</b>\n〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️\nСповіщення "
    work_mode, send_lesson_mode, end_lesson_noti, end_lesson_noti_mode, end_lesson_noti_schedule = user

    if not work_mode:
        text += "вимкнено."
        markup.add(telebot.types.InlineKeyboardButton("Увімкнути сповіщення", callback_data="turn_on"))
    else:
        text += "увімкнено "
        markup.add(telebot.types.InlineKeyboardButton("Вимкнути сповіщення", callback_data="turn_off"))
        if send_lesson_mode:
            text += "про всі заняття"
            markup.add(telebot.types.InlineKeyboardButton("Повідомляти тільки про пари", callback_data="chenge_data/send_lesson_mode/0"))
        else:
            text += "тільки про пари"
            markup.add(telebot.types.InlineKeyboardButton("Повідомляти про всі заняття", callback_data="chenge_data/send_lesson_mode/1"))

        text += ".\nПовідомлення про останню пару "
        if not end_lesson_noti:
            text += "вимкнені."
            markup.add(telebot.types.InlineKeyboardButton("Увімкнути повідомлення про останню пару", callback_data="chenge_data/end_lesson_noti/1"))
        else:
            text += "увімкнені. Надсилаються "
            markup.add(telebot.types.InlineKeyboardButton("Вимкнути повідомлення про останню пару", callback_data="chenge_data/end_lesson_noti/0"))
            if end_lesson_noti_mode:
                text += "після останньої пари"
                markup.add(telebot.types.InlineKeyboardButton("Повідомляти перед останньою парою", callback_data="chenge_data/end_lesson_noti_mode/0"))
            else:
                text += "перед останньою парою"
                markup.add(telebot.types.InlineKeyboardButton("Повідомляти після останньої парі", callback_data="chenge_data/end_lesson_noti_mode/1"))
            if end_lesson_noti_schedule:
                text += ", з розкладом на наступний день."
                markup.add(telebot.types.InlineKeyboardButton("Не надсилати розклад в кінці пар", callback_data="chenge_data/end_lesson_noti_shedule/0"))
            else:
                text += ", без розкладу на наступний день."
                markup.add(telebot.types.InlineKeyboardButton("Надсилати розклад на завтра", callback_data="chenge_data/end_lesson_noti_shedule/1"))

    markup.add(telebot.types.InlineKeyboardButton("🔙", callback_data="settings"))
    app.bot.edit_message_text(chat_id=message.chat.id, message_id=get_message_id(message), text=text, reply_markup=markup, parse_mode="HTML")


def change_user_data(app, chat_id: int, column_name: str, data: str) -> None:
    app.db.update_user_column(chat_id, column_name, data)


def set_bot_mode(app, mode: int, message) -> None:
    app.db.update_user_column(message.chat.id, "work_mode", mode)
    if mode == 0:
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("Увімкнути", callback_data="turn_on"))
        msg_id = get_message_id(message)
        if msg_id is not None:
            app.bot.edit_message_text(chat_id=message.chat.id, message_id=msg_id, text="Сповіщення вимкнено!", reply_markup=markup)
        else:
            app.bot.send_message(message.chat.id, "Сповіщення вимкнено!", reply_markup=markup, disable_notification=True)
    else:
        show_notification_settings(app, message)
