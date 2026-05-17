from teleeu_bot.utils.parsing import find_day, find_group, found_type, parse_user_group


def test_find_day_two_digits():
    assert find_day("Понеділок, 11 травня") == "11"


def test_find_day_one_digit():
    assert find_day("Понеділок, 5 травня") == "05"


def test_find_group_basic():
    assert find_group("Група 123/4 он") == "123/4_on"


def test_found_type_by_audience():
    assert found_type("", "Zoom") == "zoom"


def test_found_type_by_lesson_type():
    assert found_type("пр", "302") == "meet"


def test_parse_user_group():
    assert parse_user_group("123/4_on") == (1, 2, "34_on")
