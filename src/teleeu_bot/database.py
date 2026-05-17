from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .models import ActiveUser, UserProfile


class Database:
    ALLOWED_UPDATE_COLUMNS = {
        "work_mode",
        "send_lesson_mode",
        "end_lesson_noti",
        "end_lesson_noti_mode",
        "end_lesson_noti_shedule",
    }

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_schema(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    chat_id INTEGER,
                    first_name TEXT,
                    last_name TEXT,
                    username TEXT,
                    faculty TEXT,
                    edu_form TEXT,
                    faculty_num INTEGER,
                    admission_year INTEGER,
                    subgroup_num TEXT,
                    work_mode INTEGER,
                    send_lesson_mode INTEGER,
                    end_lesson_noti INTEGER,
                    end_lesson_noti_mode INTEGER,
                    end_lesson_noti_shedule INTEGER
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS admins (
                    chat_id INTEGER PRIMARY KEY
                )
                """
            )

    def is_registered(self, chat_id: int) -> bool:
        with self.connect() as conn:
            row = conn.execute("SELECT 1 FROM users WHERE chat_id = ? LIMIT 1", (chat_id,)).fetchone()
        return row is not None

    def get_profiles(self, chat_id: int) -> list[UserProfile]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT chat_id, first_name, last_name, username, faculty, edu_form, faculty_num,
                       admission_year, subgroup_num, work_mode, send_lesson_mode, end_lesson_noti,
                       end_lesson_noti_mode, end_lesson_noti_shedule
                FROM users
                WHERE chat_id = ?
                """,
                (chat_id,),
            ).fetchall()
        return [UserProfile.from_row(row) for row in rows]

    def create_profile(
        self,
        *,
        chat_id: int,
        first_name: str | None,
        last_name: str | None,
        username: str | None,
        faculty: str,
        edu_form: str,
        faculty_num: int,
        admission_year: int,
        subgroup_num: str,
        send_lesson_mode: int,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO users (
                    chat_id, first_name, last_name, username, faculty, edu_form, faculty_num,
                    admission_year, subgroup_num, work_mode, send_lesson_mode, end_lesson_noti,
                    end_lesson_noti_mode, end_lesson_noti_shedule
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chat_id,
                    first_name,
                    last_name,
                    username,
                    faculty,
                    edu_form,
                    faculty_num,
                    admission_year,
                    subgroup_num,
                    1,
                    send_lesson_mode,
                    1,
                    1,
                    1,
                ),
            )

    def delete_profiles(self, chat_id: int) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM users WHERE chat_id = ?", (chat_id,))

    def update_user_column(self, chat_id: int, column_name: str, value: int | str) -> None:
        if column_name not in self.ALLOWED_UPDATE_COLUMNS:
            raise ValueError(f"Column '{column_name}' cannot be updated from callback data")
        with self.connect() as conn:
            conn.execute(f"UPDATE users SET {column_name} = ? WHERE chat_id = ?", (value, chat_id))

    def get_notification_settings(self, chat_id: int) -> tuple[int, int, int, int, int] | None:
        with self.connect() as conn:
            return conn.execute(
                """
                SELECT work_mode, send_lesson_mode, end_lesson_noti, end_lesson_noti_mode,
                       end_lesson_noti_shedule
                FROM users
                WHERE chat_id = ?
                LIMIT 1
                """,
                (chat_id,),
            ).fetchone()

    def get_active_users(self) -> list[ActiveUser]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT chat_id, faculty, edu_form, faculty_num, admission_year, subgroup_num,
                       send_lesson_mode, end_lesson_noti, end_lesson_noti_mode,
                       end_lesson_noti_shedule
                FROM users
                WHERE work_mode = 1
                """
            ).fetchall()
        return [ActiveUser.from_row(row) for row in rows]

    def is_admin(self, chat_id: int) -> bool:
        with self.connect() as conn:
            row = conn.execute("SELECT 1 FROM admins WHERE chat_id = ?", (chat_id,)).fetchone()
        return row is not None
