"""Persistent group configuration."""
import json
from copy import deepcopy
from pathlib import Path
from uuid import uuid4
from PySide6.QtCore import QObject, Slot
from loguru import logger
from .dirs import CONFIG_DIR

DEFAULT_CONFIG = {"groups": []}

class GroupsConfig(QObject):
    _instance = None
    @classmethod
    def instance(cls): return cls._instance
    def __init__(self, parent=None):
        super().__init__(); GroupsConfig._instance = self
        self.file = Path(CONFIG_DIR) / "groups.json"; self.load_config()
    def load_config(self):
        try:
            data = json.loads(self.file.read_text(encoding="utf-8")) if self.file.exists() else deepcopy(DEFAULT_CONFIG)
            if not isinstance(data, dict) or not isinstance(data.get("groups"), list): raise ValueError("groups must be a list")
        except Exception as e:
            logger.warning(f"读取小组配置失败，使用默认配置: {e}"); data = deepcopy(DEFAULT_CONFIG)
        for g in data["groups"]:
            if isinstance(g, dict):
                g.setdefault("id", str(uuid4())); g.setdefault("name", "未命名小组"); g.setdefault("weight", 1.0); g.setdefault("enabled", True); g.setdefault("member_ids", [])
        self.config_write = deepcopy(data); self.config_read = deepcopy(data)
        self.save_config()
    @Slot()
    def save_config(self):
        Path(CONFIG_DIR).mkdir(parents=True, exist_ok=True); self.file.write_text(json.dumps(self.config_write, ensure_ascii=False, indent=2), encoding="utf-8"); self.config_read = deepcopy(self.config_write)
    @Slot()
    def reload_config(self): self.load_config()
    @Slot(result=bool)
    def has_unsaved_changes(self): return self.config_write != self.config_read
    @Slot(result=list)
    def get_groups(self): return deepcopy(self.config_read.get("groups", []))
    @Slot(result=list)
    def get_write_groups(self): return deepcopy(self.config_write.get("groups", []))
    @Slot(result=list)
    def get_enabled_groups(self): return [g for g in self.get_groups() if g.get("enabled") and float(g.get("weight", 0)) > 0]
    @Slot(str, result=dict)
    def get_single_group(self, gid): return next((deepcopy(g) for g in self.get_groups() if g.get("id") == gid), {})
    @Slot(str, float, bool)
    def add_group(self, name, weight=1.0, enabled=True): self.config_write["groups"].append({"id": str(uuid4()), "name": (name or "未命名小组").strip(), "weight": max(0.0, float(weight)), "enabled": bool(enabled), "member_ids": []})
    @Slot(str)
    def remove_group(self, gid): self.config_write["groups"] = [g for g in self.config_write["groups"] if g.get("id") != gid]
    @Slot(str, str, float, bool)
    def update_group(self, gid, name, weight, enabled):
        for g in self.config_write["groups"]:
            if g.get("id") == gid: g.update(name=(name or "未命名小组").strip(), weight=max(0.0, float(weight)), enabled=bool(enabled)); return
    @Slot(str, list)
    def set_members(self, gid, members):
        for g in self.config_write["groups"]:
            if g.get("id") == gid: g["member_ids"] = list(dict.fromkeys(str(x) for x in (members or []))); return
