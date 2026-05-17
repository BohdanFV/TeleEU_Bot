from __future__ import annotations

import datetime as dt
import json
import logging
import time
from pathlib import Path
from typing import Any

import requests

from ..config import Settings
from ..database import Database
from ..models import ScheduleEntry
from ..utils.dates import build_group_name
from ..utils.parsing import MONTHS, find_day, find_group, find_most_similar_month, found_type
from .links import LinkService

logger = logging.getLogger(__name__)

ScheduleData = dict[str, Any]


class ScheduleService:
    def __init__(self, settings: Settings, db: Database, links: LinkService) -> None:
        self.settings = settings
        self.db = db
        self.links = links
        self.schedules_dir = settings.data_dir / "schedules"
        self.faculties_file = settings.data_dir / "faculties" / "faculties.json"

    def schedule_path(self, now: dt.datetime) -> Path:
        return self.schedules_dir / f"shedule_{now.strftime('%Y_%W')}.json"

    def load_faculties(self) -> list[dict[str, Any]]:
        with self.faculties_file.open("r", encoding="utf-8") as file:
            return json.load(file)

    def load_schedule(self, now: dt.datetime) -> ScheduleData | None:
        try:
            with self.schedule_path(now).open("r", encoding="utf-8") as file:
                schedule_data: ScheduleData = json.load(file)

            if self.settings.update_schedule_every_day:
                updated_at = dt.datetime.fromisoformat(schedule_data.get("updatetime", "1970-01-01T00:00:00"))
                if updated_at.date() != now.date():
                    return self.update_schedule(now)
            return schedule_data
        except FileNotFoundError:
            logger.info("No schedule file for current week. Updating schedule.")
            return self.update_schedule(now)
        except Exception:
            logger.exception("Failed to load schedule")
            return self.update_schedule(now)

    def get_user_schedule(self, chat_id: int, now: dt.datetime) -> tuple[list[ScheduleEntry], list[str]]:
        profiles = self.db.get_profiles(chat_id)
        schedule_data = self.load_schedule(now)
        if not profiles or not schedule_data:
            return [], []

        result: list[ScheduleEntry] = []
        missing_groups: list[str] = []
        for profile in profiles:
            group = build_group_name(
                now,
                profile.faculty_num,
                profile.admission_year,
                profile.subgroup_num,
                self.settings.month_of_course_change,
                self.settings.day_of_course_change,
            )
            group_schedule = (
                schedule_data.get(profile.faculty, {})
                .get(profile.edu_form, {})
                .get(group)
            )
            if group_schedule:
                result.append(ScheduleEntry(group=group, datetime_context=now, schedule=group_schedule))
            else:
                missing_groups.append(f"{group} ({profile.faculty} {profile.edu_form})")
        return result, missing_groups

    def week_days(self, now: dt.datetime, week_shift: int = 0) -> list[dt.datetime]:
        start = now - dt.timedelta(days=now.weekday()) + dt.timedelta(days=7 * week_shift)
        return [start + dt.timedelta(days=i) for i in range(6)]

    def format_messages(
        self,
        entries: list[ScheduleEntry],
        days: list[dt.datetime],
        links_data: dict[str, dict[str, str]] | None = None,
        now: dt.datetime | None = None,
    ) -> list[str]:
        if not entries:
            return []
        now = now or dt.datetime.now()
        messages: list[str] = []
        day_titles = (
            "<b>Понеділок:</b>",
            "<b>Вівторок:</b>",
            "<b>Середа:</b>",
            "<b>Четвер:</b>",
            "<b>П'ятниця:</b>",
            "<b>Субота:</b>",
            "<b>Неділя:</b>",
        )

        for entry in entries:
            if len(entries) > 1:
                messages.append(f"<b>&lt;&lt;=== Група {entry.group} ===&gt;&gt;</b>")
            target_days = days or [dt.datetime.strptime(f"{day}/{entry.datetime_context.year}", "%d.%m/%Y") for day in sorted(entry.schedule)]

            for day in target_days:
                text = day_titles[day.weekday()]
                if day.date() < now.date():
                    text += " ✔"
                elif day.date() == now.date():
                    text += " <b>Today 🔘</b>"
                elif day.date() == (now + dt.timedelta(days=1)).date():
                    text += " <b>Tomorrow</b>"
                else:
                    text += day.strftime(" %d.%m")

                if day.weekday() == 6:
                    text += "\nЧас відпочинку та розваг! 🎉 Гарного вам відпочинку!"

                lesson_day = entry.schedule.get(day.strftime("%d.%m"), {})
                for lesson_time, lesson in lesson_day.items():
                    text += self._format_lesson(lesson_time, lesson, links_data or {})
                messages.append(text)
        return messages

    def _format_lesson(self, lesson_time: str, lesson: dict[str, Any], links_data: dict[str, dict[str, str]]) -> str:
        str_lesson_time = lesson_time
        if lesson.get("endtime"):
            str_lesson_time += f" - {lesson['endtime']}"
        text = f"\n〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️\n{str_lesson_time} / {lesson.get('type', '')} / {lesson.get('audience', '')}\n"

        subject = str(lesson.get("subject", "")).replace("\n", " ")
        lesson_kind = found_type(lesson.get("type"), lesson.get("audience"), self.settings.lesson_type_keywords)
        link = self.links.lesson_link(lesson, links_data) if links_data else ""

        if link:
            if lesson_kind == "meet":
                return text + f"<a href='{link}'><b>{subject}</b></a>"
            if lesson_kind == "zoom":
                return text + f"<a href='{link}'>{subject}</a>"
            return text + f"<a href='{link}'><i>{subject}</i></a>"
        return text + f"<i>{subject}</i>"

    def next_lesson_time(self, schedule_data: ScheduleData, now: dt.datetime) -> dt.datetime | None:
        next_time: dt.datetime | None = None
        for schedule_date, times in schedule_data.get("times", {}).items():
            for schedule_time in times:
                if not schedule_date or not schedule_time:
                    continue
                try:
                    candidate = dt.datetime.strptime(f"{schedule_date},{schedule_time},{now.year}", "%d.%m,%H:%M,%Y")
                except ValueError:
                    logger.warning("Invalid schedule time: %s %s", schedule_date, schedule_time)
                    continue
                if candidate > now and (next_time is None or candidate < next_time):
                    next_time = candidate
        return next_time

    def update_schedule(self, now: dt.datetime) -> ScheduleData | None:
        for attempt in range(self.settings.schedule_attempts):
            try:
                downloaded = (
                    self._download_schedule_cached_for_tests(now)
                    if self.settings.test_mode and not self.settings.test_update_request
                    else self._download_schedule(now)
                )
                data = self._save_schedule(downloaded, now)
                logger.info("Schedule updated")
                return data
            except Exception:
                logger.exception("Failed to update schedule, attempt %s", attempt + 1)
                time.sleep(self.settings.schedule_attempt_pause)
        return None

    def _download_schedule_cached_for_tests(self, now: dt.datetime) -> list[dict[str, Any]]:
        cache_path = self.settings.data_dir / "tmp" / "request_shedule_data.json"
        try:
            with cache_path.open("r", encoding="utf-8") as file:
                cached_data: list[dict[str, Any]] = json.load(file)
                return cached_data
        except FileNotFoundError:
            downloaded = self._download_schedule(now)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with cache_path.open("w", encoding="utf-8") as file:
                json.dump(downloaded, file, ensure_ascii=False, indent=2)
            return downloaded

    def _download_schedule(self, now: dt.datetime) -> list[dict[str, Any]]:
        if not self.settings.google_api_key:
            raise RuntimeError("GOOGLE_API_KEY is required to update schedule from Google Sheets")

        monday = now - dt.timedelta(days=now.weekday())
        week_variants = {
            f"{monday.day}.{monday.month}",
            f"{monday.strftime('%d')}.{monday.month}",
            f"{monday.strftime('%d')}.{monday.strftime('%m')}",
            f"{monday.day}.{monday.strftime('%m')}",
        }
        headers = {
            "Accept": "*/*",
            "Origin": "https://shedulem.e-u.edu.ua",
            "Referer": "https://shedulem.e-u.edu.ua/",
            "User-Agent": "Mozilla/5.0",
        }

        faculties = requests.get(self.settings.faculties_source_url, headers=headers, timeout=30).json()
        downloaded_data: list[dict[str, Any]] = []
        for faculty in faculties:
            page_data = {"fac": faculty, "data": {}}
            for education_form in ["denna", "zaochna"]:
                spreadsheet_id = faculty.get(education_form)
                if not spreadsheet_id:
                    continue
                pages_list = requests.get(
                    f"{self.settings.google_sheets_api_base_url}/{spreadsheet_id}",
                    params={"key": self.settings.google_api_key},
                    headers=headers,
                    timeout=30,
                ).json()
                params: dict[str, Any] = {"ranges": [], "key": self.settings.google_api_key}
                for sheet in pages_list.get("sheets", []):
                    title = sheet.get("properties", {}).get("title", "")
                    hidden = sheet.get("properties", {}).get("hidden") is True
                    if not hidden and any(week_variant in title for week_variant in week_variants):
                        params["ranges"].append(f"{title}!3:100")
                if params["ranges"]:
                    response = requests.get(
                        f"{self.settings.google_sheets_api_base_url}/{spreadsheet_id}/values:batchGet",
                        params=params,
                        headers=headers,
                        timeout=60,
                    )
                    response.raise_for_status()
                    page_data["data"][education_form] = response.json()
            downloaded_data.append(page_data)
        return downloaded_data

    def _save_schedule(self, downloaded_data: list[dict[str, Any]], now: dt.datetime) -> ScheduleData:
        data: ScheduleData = {"updatetime": now.isoformat(), "times": {}}

        for page_data in downloaded_data:
            faculty = page_data["fac"]
            faculty_id = faculty["id"]
            data.setdefault(faculty_id, {})
            for education_form, response_json in page_data["data"].items():
                data[faculty_id].setdefault(education_form, {})
                for page in response_json.get("valueRanges", []):
                    values = page.get("values", [])
                    if not values:
                        continue
                    for column in range(3, len(values[0]), 3):
                        fgroup = find_group(values[0][column])
                        if not fgroup:
                            continue
                        group = fgroup.replace("/", "")
                        data[faculty_id][education_form][group] = {}
                        week_day = ""
                        day = ""
                        month = ""
                        for row in range(1, len(values)):
                            row_values = values[row]
                            if len(row_values) > 1 and row_values[1]:
                                day = find_day(row_values[1]) or day
                                month = find_most_similar_month(row_values[1]) or month
                                if month in MONTHS:
                                    week_day = f"{day}.{MONTHS.index(month) + 1:02d}"
                                if not (day and month):
                                    logger.warning("Cannot parse date for group %s from %r", group, row_values[1])
                            if column < len(row_values) and row_values[column]:
                                if len(row_values) <= 2:
                                    continue
                                tm = row_values[2].replace(" ", "").split("-")
                                start_time = tm[0]
                                data["times"].setdefault(week_day, [])
                                if start_time not in data["times"][week_day]:
                                    data["times"][week_day].append(start_time)
                                data[faculty_id][education_form][group].setdefault(week_day, {})
                                lesson = {"subject": row_values[column]}
                                if column + 1 < len(row_values):
                                    lesson["type"] = row_values[column + 1]
                                if column + 2 < len(row_values):
                                    lesson["audience"] = row_values[column + 2]
                                if len(tm) >= 2:
                                    lesson["endtime"] = tm[1]
                                data[faculty_id][education_form][group][week_day][start_time] = lesson

        for times_day in data["times"]:
            data["times"][times_day] = sorted(data["times"][times_day])
        self.schedules_dir.mkdir(parents=True, exist_ok=True)
        with self.schedule_path(now).open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        return data
