from pathlib import Path

import pytest

import core.choice as choice_module
from core.choice import ChoiceMaker
from core.config.groups import GroupsConfig
from core.config.memory import MemoryConfig
from core.config.settings import SettingsConfig
from core.config.students import StudentsConfig
from core.integration import NotificationManager
from core.integration.classisland import ClassIslandIntegration


class FakeStudents:
    def __init__(self):
        self.students = [
            {"id": "a", "name": "A", "weight": 1, "enabled": True, "properties": [], "avatar": ""},
            {"id": "b", "name": "B", "weight": 1, "enabled": True, "properties": [], "avatar": ""},
            {"id": "c", "name": "C", "weight": 1, "enabled": True, "properties": [], "avatar": ""},
        ]

    def get_students(self):
        return self.students

    def get_enabled_students(self):
        return [student["id"] for student in self.students if student["enabled"]]

    def get_partof_students_weights(self, student_ids):
        return [1 for _ in student_ids]

    def get_single_student(self, student_id):
        return next(student for student in self.students if student["id"] == student_id)

    def getProperty(self, student_id):
        return []

    def getAvatarPath(self, student_id):
        return ""


class FakeSettings:
    def __init__(self, persistent=True, by_subject=True):
        self.persistent = persistent
        self.by_subject = by_subject

    def getCiMemoryPersistent(self):
        return self.persistent

    def getCiMemoryBySubject(self):
        return self.by_subject


class FakeClassIsland:
    def __init__(self):
        self.subject = "语文"

    def get_current_subject(self):
        return self.subject


class FakeNotificationManager:
    def send(self, *args, **kwargs):
        return None


@pytest.fixture
def choice(tmp_path, monkeypatch):
    students = FakeStudents()
    settings = FakeSettings()
    class_island = FakeClassIsland()

    monkeypatch.setattr(StudentsConfig, "instance", classmethod(lambda cls: students))
    monkeypatch.setattr(GroupsConfig, "instance", classmethod(lambda cls: object()))
    monkeypatch.setattr(SettingsConfig, "instance", classmethod(lambda cls: settings))
    monkeypatch.setattr(ClassIslandIntegration, "instance", classmethod(lambda cls: class_island))
    monkeypatch.setattr(NotificationManager, "instance", classmethod(lambda cls: FakeNotificationManager()))

    original_init = MemoryConfig.__init__

    def init_with_temp_file(self, student_ids=None, file=None):
        original_init(self, student_ids, Path(tmp_path) / "memory.json")

    monkeypatch.setattr(MemoryConfig, "__init__", init_with_temp_file)
    monkeypatch.setattr(choice_module, "choices", lambda population, weights, k: [population[0]])

    picker = ChoiceMaker()
    picker.memoryEnabled = True
    return picker


def test_same_subject_history_survives_runtime_toggle(choice):
    first = choice.choosePeople(1, False)[0]["id"]
    choice.memoryEnabled = False
    choice.memoryEnabled = True
    second = choice.choosePeople(1, False)[0]["id"]

    assert first == "a"
    assert second == "b"


def test_subjects_use_independent_partitions(choice):
    chinese = choice.choosePeople(1, False)[0]["id"]
    choice.classIsland.subject = "数学"
    math = choice.choosePeople(1, False)[0]["id"]

    assert chinese == "a"
    assert math == "a"
    assert choice.memoryConfig.get("语文") == {"a"}
    assert choice.memoryConfig.get("数学") == {"a"}
