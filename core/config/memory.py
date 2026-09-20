"""Persistent, subject-partitioned picker memory."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

from loguru import logger

from .dirs import CONFIG_DIR


class MemoryConfig:
    """Store remembered student GUIDs grouped by a subject key.

    The class deliberately has no dependency on ``StudentsConfig``.  Callers
    provide a callback returning the currently known student IDs so stale IDs
    can be discarded while loading.  The callback is optional for callers
    that need to inspect or migrate a memory file before student data exists.
    """

    DEFAULT_KEY = "__default__"
    _instance: "MemoryConfig | None" = None

    @classmethod
    def instance(cls) -> "MemoryConfig":
        """Return the process-wide default memory configuration."""
        if cls._instance is None:
            cls()
        return cls._instance

    def __init__(
        self,
        student_ids: Callable[[], Iterable[str]] | None = None,
        file: Path | None = None,
    ) -> None:
        self.student_ids = student_ids
        self.file = Path(file) if file is not None else Path(CONFIG_DIR) / "memory.json"
        self._subjects: dict[str, set[str]] = {}
        MemoryConfig._instance = self
        self.reload()

    @classmethod
    def _normalize_key(cls, subject_key: Any) -> str:
        """Return a stable key, using the fallback partition for blank input."""
        if subject_key is None:
            return cls.DEFAULT_KEY
        try:
            key = str(subject_key).strip()
        except Exception:
            key = ""
        return key or cls.DEFAULT_KEY

    def _known_student_ids(self) -> set[str] | None:
        """Read and normalize known IDs, returning ``None`` when unfiltered."""
        if self.student_ids is None:
            return None
        try:
            values = self.student_ids()
            if values is None:
                return set()
            return {str(value) for value in values if value is not None and str(value)}
        except Exception:
            logger.exception("读取学生 GUID 列表失败，记忆将不执行学生过滤。")
            return None

    def _normalize_subjects(self, data: Any) -> dict[str, set[str]]:
        """Parse the persisted shape defensively and remove stale IDs."""
        if not isinstance(data, dict):
            return {}
        subjects = data.get("subjects")
        if not isinstance(subjects, dict):
            return {}

        known_ids = self._known_student_ids()
        normalized: dict[str, set[str]] = {}
        for raw_key, raw_ids in subjects.items():
            if not isinstance(raw_ids, (list, tuple, set)):
                continue
            key = self._normalize_key(raw_key)
            ids = {
                str(value)
                for value in raw_ids
                if value is not None and str(value)
            }
            if known_ids is not None:
                ids.intersection_update(known_ids)
            normalized.setdefault(key, set()).update(ids)
        return normalized

    def get(self, subject_key: str) -> set[str]:
        """Return a copy of the remembered IDs for ``subject_key``."""
        key = self._normalize_key(subject_key)
        return set(self._subjects.get(key, set()))

    def add(self, subject_key: str, student_ids: Iterable[str]) -> None:
        """Add student IDs to one partition without writing the file."""
        key = self._normalize_key(subject_key)
        if student_ids is None:
            return
        try:
            ids = {
                str(value)
                for value in student_ids
                if value is not None and str(value)
            }
        except (TypeError, ValueError):
            logger.exception("写入学生记忆失败，忽略无效 GUID 列表。")
            return
        if ids:
            self._subjects.setdefault(key, set()).update(ids)

    def clear(self, subject_key: str | None = None) -> None:
        """Clear one partition, or all partitions when no key is supplied."""
        if subject_key is None:
            self._subjects.clear()
            return
        self._subjects.pop(self._normalize_key(subject_key), None)

    def reload(self) -> None:
        """Load the file, replacing the in-memory state atomically."""
        try:
            if not self.file.exists():
                parsed: Any = {"subjects": {}}
                replacement = self._normalize_subjects(parsed)
                self._subjects = replacement
                self.save()
                return
            with self.file.open("r", encoding="utf-8") as stream:
                parsed = json.load(stream)
            replacement = self._normalize_subjects(parsed)
        except Exception:
            logger.exception("读取抽选记忆文件失败，将使用空记忆。")
            replacement = {}
        self._subjects = replacement

    def save(self) -> None:
        """Persist all partitions as JSON, creating the parent directory."""
        try:
            self.file.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "subjects": {
                    key: sorted(ids)
                    for key, ids in sorted(self._subjects.items())
                    if ids
                }
            }
            self.file.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            logger.exception("保存抽选记忆文件失败。")

