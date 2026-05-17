from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class UserProfile:
    chat_id: int
    first_name: str | None
    last_name: str | None
    username: str | None
    faculty: str
    edu_form: str
    faculty_num: int
    admission_year: int
    subgroup_num: str
    work_mode: int
    send_lesson_mode: int
    end_lesson_noti: int
    end_lesson_noti_mode: int
    end_lesson_noti_schedule: int

    @classmethod
    def from_row(cls, row: tuple[Any, ...]) -> "UserProfile":
        return cls(*row)


@dataclass(frozen=True)
class ActiveUser:
    chat_id: int
    faculty: str
    edu_form: str
    faculty_num: int
    admission_year: int
    subgroup_num: str
    send_lesson_mode: int
    end_lesson_noti: int
    end_lesson_noti_mode: int
    end_lesson_noti_schedule: int

    @classmethod
    def from_row(cls, row: tuple[Any, ...]) -> "ActiveUser":
        return cls(*row)


@dataclass(frozen=True)
class ScheduleEntry:
    group: str
    datetime_context: Any
    schedule: dict[str, Any]
