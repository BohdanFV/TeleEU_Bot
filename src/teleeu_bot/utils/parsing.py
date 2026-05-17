from __future__ import annotations

import re
from typing import Mapping, Sequence

MONTHS = [
    "січня",
    "лютого",
    "березня",
    "квітня",
    "травня",
    "червня",
    "липня",
    "серпня",
    "вересня",
    "жовтня",
    "листопада",
    "грудня",
]

KEY_WORDS = {
    "zoom": {"л", "лекція", "ккр", "шк", "захист", "іспит", "шкзалік"},
    "meet": {"пр", "практична", "прзалік", "залік", "лаб"},
}


def find_most_similar_month(input_str: str) -> str | None:
    input_str = input_str.lower()
    best_match = None
    best_similarity = 0

    for month in MONTHS:
        for i in range(max(len(input_str) - len(month) + 1, 1)):
            substring = input_str[i : i + len(month)]
            similarity = sum(1 for left, right in zip(substring, month) if left == right)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = month
    return best_match


def find_day(input_str: str) -> str:
    value = f" {input_str} "
    for i in range(len(value) - 3):
        if not value[i].isdigit() and value[i + 1].isdigit() and value[i + 2].isdigit() and not value[i + 3].isdigit():
            return value[i + 1 : i + 3]
        if not value[i].isdigit() and value[i + 1].isdigit() and not value[i + 2].isdigit():
            return "0" + value[i + 1 : i + 2]
    return ""


def find_group(text: str) -> str | None:
    def find_group_num() -> str | None:
        length = len(text)
        i = 0
        while i < length:
            if i - 1 < 0 or not text[i - 1].isdigit():
                if i + 2 < length and text[i : i + 3].isdigit():
                    if i + 4 < length and text[i + 3] == "/" and text[i + 4].isdigit():
                        if i + 5 < length and text[i + 5].isdigit():
                            if i + 6 >= length or not text[i + 6].isdigit():
                                return text[i : i + 6]
                        if i + 5 >= length or not text[i + 5].isdigit():
                            return text[i : i + 5]
                    if i + 3 >= length or not text[i + 3].isdigit():
                        return text[i : i + 3]
            i += 1

        i = 0
        while i < length:
            if text[i].isdigit():
                group = ""
                while i < length and text[i].isdigit():
                    group += text[i]
                    i += 1
                return group
            i += 1
        return None

    group_num = find_group_num()
    if group_num is None:
        return None

    sep = {" ", "\n"}
    i = 0
    while i + 1 < len(text):
        if (i - 1 < 0 or text[i - 1] in sep) and text[i] == "о" and (i + 2 >= len(text) or text[i + 2] in sep):
            if text[i + 1] == "ф":
                return f"{group_num}_of"
            if text[i + 1] == "н":
                return f"{group_num}_on"
        i += 1
    return group_num


def parse_user_group(value: str) -> tuple[int, int, str] | None:
    group = value.replace(" ", "")
    pattern = r"^(/(\d{3,5})|(\d{3,5})|(\d{3}/\d{1,2}))(_of|_on)?$"
    if not re.match(pattern, group):
        return None
    if group.startswith("/"):
        group = group[1:]
    split_group = group.replace("/", "").split("_")
    faculty_num = int(split_group[0][0])
    course_num = int(split_group[0][1])
    subgroup = "_".join(s[2:] if i == 0 else s for i, s in enumerate(split_group))
    return faculty_num, course_num, subgroup


def _normalize_keywords(key_words: Mapping[str, Sequence[str]] | None = None) -> dict[str, set[str]]:
    source = key_words or KEY_WORDS
    return {key: {str(item).lower().replace(" ", "") for item in values} for key, values in source.items()}


def found_type(
    event_type: str | None,
    audience: str | None = None,
    key_words: Mapping[str, Sequence[str]] | None = None,
) -> str | None:
    event_type_lower = (event_type or "").lower().replace(" ", "")
    audience_lower = (audience or "").lower().replace(" ", "")
    normalized_keywords = _normalize_keywords(key_words)

    if "zoom" in audience_lower:
        return "zoom"
    if "meet" in audience_lower:
        return "meet"
    if event_type_lower in normalized_keywords.get("zoom", set()):
        return "zoom"
    if event_type_lower in normalized_keywords.get("meet", set()):
        return "meet"
    return None


def found_teacher(input_string: str, links: Mapping[str, dict[str, str]]) -> str | None:
    lines = input_string.split("\n")
    lines.reverse()
    extracted_text: list[str] = []

    for line in lines:
        for word in line.split():
            if word and word[0].isupper():
                extracted_text.append(word)
            elif extracted_text:
                extracted_text.append(word)
        if extracted_text:
            break

    if not extracted_text:
        return None

    candidates = [teacher for teacher in links if extracted_text[0] in teacher]
    if len(candidates) > 1 and len(extracted_text) > 1:
        candidates = [teacher for teacher in candidates if extracted_text[1] in teacher]
    return candidates[0] if candidates else None
