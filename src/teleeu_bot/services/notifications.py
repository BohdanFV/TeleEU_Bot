from __future__ import annotations

import datetime as dt
import logging
import time
from typing import Any

import telebot

from ..models import ScheduleEntry
from ..utils.dates import build_group_name
from ..utils.parsing import found_type

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, app) -> None:
        self.app = app

    def run_forever(self) -> None:
        now = self.app.now()
        next_lesson_time = now
        while True:
            next_lesson_time = self.handle_time(next_lesson_time)
            sleep_time = max((next_lesson_time - self.app.now()).total_seconds(), 1)
            logger.info("Sleep to: %s", next_lesson_time)
            if self.app.settings.test_mode:
                sleep_time /= max(self.app.settings.test_speed_time, 1)
            time.sleep(sleep_time)

    def handle_time(self, now: dt.datetime) -> dt.datetime:
        now = now + dt.timedelta(minutes=self.app.settings.notify_before_minutes)
        schedule_data = self.app.schedule_service.load_schedule(now)
        links_data = self.app.link_service.load()

        if schedule_data and links_data:
            today_times = schedule_data.get("times", {}).get(now.strftime("%d.%m"), [])
            if now.strftime("%H:%M") in today_times:
                self.send_lesson(schedule_data, links_data, now)

        if schedule_data:
            next_time = self.app.schedule_service.next_lesson_time(schedule_data, now)
            if next_time:
                return next_time - dt.timedelta(minutes=self.app.settings.notify_before_minutes)

        real_now = self.app.real_now()
        days_to_monday = (7 - real_now.weekday()) % 7
        return (real_now + dt.timedelta(days=days_to_monday)).replace(hour=0, minute=5, second=0, microsecond=0)

    def send_lesson(self, schedule_data: dict[str, Any], links_data: dict[str, dict[str, str]], now: dt.datetime) -> None:
        users = self.app.db.get_active_users()
        str_day = now.strftime("%d.%m")
        str_time = now.strftime("%H:%M")

        for _ in range(self.app.settings.notification_attempts):
            sent_indexes: list[int] = []
            for index, user in enumerate(users):
                try:
                    group = build_group_name(
                        now,
                        user.faculty_num,
                        user.admission_year,
                        user.subgroup_num,
                        self.app.settings.month_of_course_change,
                        self.app.settings.day_of_course_change,
                    )
                    group_data = schedule_data.get(user.faculty, {}).get(user.edu_form, {}).get(group, {})
                    lesson = group_data.get(str_day, {}).get(str_time)
                    if lesson:
                        self._send_lesson_message(user, lesson, links_data, str_time)
                        self._send_last_lesson_message(user, group, group_data, now)
                    sent_indexes.append(index)
                except telebot.apihelper.ApiException as exc:
                    if exc.error_code == 403:
                        self.app.db.update_user_column(user.chat_id, "work_mode", 0)
                        sent_indexes.append(index)
                    elif exc.error_code == 400:
                        self.app.db.delete_profiles(user.chat_id)
                        sent_indexes.append(index)
                    else:
                        logger.exception("Telegram API error while sending lesson")
                except Exception:
                    logger.exception("Failed to send lesson notification")

            for index in reversed(sent_indexes):
                users.pop(index)
            if not users:
                break
            time.sleep(self.app.settings.notification_attempt_pause)

    def _send_lesson_message(self, user, lesson: dict[str, Any], links_data: dict[str, dict[str, str]], str_time: str) -> None:
        if not lesson.get("type") and not user.send_lesson_mode:
            return
        str_lesson_time = str_time
        if lesson.get("endtime"):
            str_lesson_time += f" - {lesson['endtime']}"
        link = ""
        if lesson.get("type"):
            link = self.app.link_service.lesson_link(lesson, links_data)
        if not link and lesson.get("type"):
            link = (
                "Посилання на цю пару не знайдено 👀\n"
                f"Можете скористатися файлом <a href='{self.app.settings.fallback_resources_url}'>🔗Навчальні ресурси</a>"
            )
        self.app.bot.send_message(
            user.chat_id,
            f"🕗 {str_lesson_time} / {lesson.get('type', '')} / {lesson.get('audience', '')}\n"
            f"👉<b>{lesson.get('subject', '')}</b>\n{link}",
            parse_mode="HTML",
            disable_notification=False,
        )

    def _send_last_lesson_message(self, user, group: str, group_data: dict[str, Any], now: dt.datetime) -> None:
        if not user.end_lesson_noti:
            return
        day_data = group_data.get(now.strftime("%d.%m"), {})
        keys = list(day_data.keys())
        if not keys:
            return
        last_index = -1
        if not user.send_lesson_mode:
            while abs(last_index) <= len(keys) and not day_data[keys[last_index]].get("type"):
                last_index -= 1
        if abs(last_index) > len(keys) or now.strftime("%H:%M") != keys[last_index]:
            return

        next_day = now
        while next_day.isocalendar()[1] == now.isocalendar()[1]:
            next_day = next_day + dt.timedelta(days=1)
            if next_day.strftime("%d.%m") in group_data:
                break
        else:
            next_day = None

        if next_day:
            text_day = "- завтра" if next_day.date() == (now + dt.timedelta(days=1)).date() else next_day.strftime("%d.%m")
            self.app.bot.send_message(
                user.chat_id,
                f"<b>Це остання пара на сьогодні.</b> Наступні заняття <b>{text_day}</b>. Гарного відпочинку! 📚🌙",
                parse_mode="HTML",
            )
            if user.end_lesson_noti_schedule:
                messages = self.app.schedule_service.format_messages(
                    [ScheduleEntry(group=group, datetime_context=now, schedule=group_data)],
                    [next_day],
                    links_data={},
                    now=now,
                )
                for message in messages:
                    self.app.bot.send_message(user.chat_id, message, parse_mode="HTML", disable_web_page_preview=True)
        else:
            self.app.bot.send_message(user.chat_id, "Це остання пара на цьому тижні. Гарного відпочинку! 📚🌙", parse_mode="HTML")
