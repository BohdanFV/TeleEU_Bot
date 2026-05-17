from __future__ import annotations

import telebot


def reply_keyboards(web_schedule_url: str) -> list[telebot.types.ReplyKeyboardMarkup]:
    keyboard_v1 = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    keyboard_v1.add(
        telebot.types.KeyboardButton("/Коди доступу"),
        telebot.types.KeyboardButton("/Налаштування"),
        telebot.types.KeyboardButton("/Розклад на сьогодні"),
        telebot.types.KeyboardButton("/Розклад на завтра"),
        telebot.types.KeyboardButton("/Розклад на цей тиждень"),
        telebot.types.KeyboardButton("/Розклад на наступний тиждень"),
    )

    keyboard_v2 = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    keyboard_v2.add(
        telebot.types.KeyboardButton("/Коди доступу"),
        telebot.types.KeyboardButton("/Налаштування"),
        telebot.types.KeyboardButton("/Розклад на сьогодні"),
        telebot.types.KeyboardButton("/Розклад на завтра"),
        telebot.types.KeyboardButton(text="Розклад", web_app=telebot.types.WebAppInfo(url=web_schedule_url)),
    )
    return [keyboard_v1, keyboard_v2]


def main_inline_keyboard(web_schedule_url: str) -> telebot.types.InlineKeyboardMarkup:
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton("Коди доступу", callback_data="access_codes"),
        telebot.types.InlineKeyboardButton("Налаштування", callback_data="settings"),
        telebot.types.InlineKeyboardButton("Розклад на сьогодні", callback_data="schedule_for_today"),
        telebot.types.InlineKeyboardButton("Розклад на завтра", callback_data="schedule_for_tomorrow"),
        telebot.types.InlineKeyboardButton("Розклад на цей тиждень", callback_data="schedule_for_week"),
        telebot.types.InlineKeyboardButton("Розклад Web", web_app=telebot.types.WebAppInfo(url=web_schedule_url)),
    )
    return markup


def not_registered_keyboard() -> telebot.types.InlineKeyboardMarkup:
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("Зареєструватись", callback_data="regist"))
    return markup
