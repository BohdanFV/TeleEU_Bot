import datetime as dt

from teleeu_bot.config import _datetime_env


def test_datetime_env_accepts_iso_datetime(monkeypatch):
    monkeypatch.setenv("TEST_FIRST_TIME", "2026-03-09T08:44:50")
    assert _datetime_env("TEST_FIRST_TIME") == dt.datetime(2026, 3, 9, 8, 44, 50)


def test_datetime_env_accepts_single_digit_day(monkeypatch):
    monkeypatch.setenv("TEST_FIRST_TIME", "2026-03-9T08:44:50")
    assert _datetime_env("TEST_FIRST_TIME") == dt.datetime(2026, 3, 9, 8, 44, 50)


def test_datetime_env_empty_means_current_time(monkeypatch):
    monkeypatch.setenv("TEST_FIRST_TIME", "")
    assert _datetime_env("TEST_FIRST_TIME") is None
