from __future__ import annotations

import datetime as dt


class AcceleratedDateTime:
    """Clock helper for local testing with accelerated time."""

    def __init__(self, initial_datetime: dt.datetime, acceleration_factor: int) -> None:
        self.base_datetime = initial_datetime
        self.start_datetime = dt.datetime.now()
        self.acceleration_factor = acceleration_factor

    def now(self) -> dt.datetime:
        elapsed = (dt.datetime.now() - self.start_datetime).total_seconds()
        return self.base_datetime + dt.timedelta(seconds=elapsed * self.acceleration_factor)


def academic_year(now: dt.datetime, change_month: int = 7, change_day: int = 1) -> int:
    """Return the academic year number for the configured transition date.

    With the default 1 July transition, dates from 01.07.2026 belong to the
    2026/2027 academic year, so the function returns 2027.
    """

    change_date = dt.date(now.year, change_month, change_day)
    return now.year + 1 if now.date() >= change_date else now.year


def admission_year_from_course(
    now: dt.datetime,
    course_num: int,
    change_month: int = 7,
    change_day: int = 1,
) -> int:
    """Calculate admission year from the course number during registration."""

    return academic_year(now, change_month, change_day) - course_num


def current_course_number(
    now: dt.datetime,
    admission_year: int,
    change_month: int = 7,
    change_day: int = 1,
) -> int:
    """Calculate current course number using configurable academic-year switch date."""

    return academic_year(now, change_month, change_day) - admission_year


def build_group_name(
    now: dt.datetime,
    faculty_num: int,
    admission_year: int,
    subgroup_num: str,
    change_month: int = 7,
    change_day: int = 1,
) -> str:
    return f"{faculty_num}{current_course_number(now, admission_year, change_month, change_day)}{subgroup_num}"
