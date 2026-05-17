from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import requests

from ..config import Settings
from ..utils.parsing import found_teacher, found_type

logger = logging.getLogger(__name__)


class LinkService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.file_path = settings.data_dir / "links" / "links.json"

    def load(self) -> dict[str, dict[str, str]]:
        for _ in range(2):
            try:
                with self.file_path.open("r", encoding="utf-8") as file:
                    return json.load(file)
            except FileNotFoundError:
                updated = self.update()
                if updated:
                    return updated
        return {}

    def update(self) -> dict[str, dict[str, str]] | None:
        if not self.settings.update_links_enabled:
            return None
        try:
            response = requests.get(
                self.settings.links_source_url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=30,
            )
            response.raise_for_status()
            data: dict[str, dict[str, str]] = response.json()
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with self.file_path.open("w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
            logger.info("Links updated")
            return data
        except Exception:
            logger.exception("Failed to update links")
            return None

    def lesson_link(self, lesson: dict[str, Any], links_data: dict[str, dict[str, str]]) -> str:
        teacher = found_teacher(str(lesson.get("subject", "")), links_data)
        link_type = found_type(lesson.get("type"), lesson.get("audience"), self.settings.lesson_type_keywords)
        if teacher and link_type:
            return links_data.get(teacher, {}).get(link_type, "")
        return ""
