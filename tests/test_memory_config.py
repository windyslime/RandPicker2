import json

from core.config.memory import MemoryConfig


def test_round_trip_filters_deleted_students(tmp_path):
    file = tmp_path / "memory.json"
    memory = MemoryConfig(student_ids=lambda: {"a", "b"}, file=file)
    memory.add("语文", ["a", "deleted"])
    memory.save()

    loaded = MemoryConfig(student_ids=lambda: {"a", "b"}, file=file)
    assert loaded.get("语文") == {"a"}


def test_clear_one_subject_does_not_clear_other_subject(tmp_path):
    memory = MemoryConfig(student_ids=lambda: {"a", "b"}, file=tmp_path / "memory.json")
    memory.add("语文", ["a"])
    memory.add("数学", ["b"])
    memory.clear("语文")
    assert memory.get("语文") == set()
    assert memory.get("数学") == {"b"}


def test_malformed_file_falls_back_to_empty_memory(tmp_path):
    file = tmp_path / "memory.json"
    file.write_text("not json", encoding="utf-8")
    memory = MemoryConfig(file=file)
    assert memory.get("语文") == set()


def test_missing_file_is_created_with_empty_structure(tmp_path):
    file = tmp_path / "nested" / "memory.json"
    MemoryConfig(file=file)
    assert json.loads(file.read_text(encoding="utf-8")) == {"subjects": {}}


def test_blank_subject_uses_default_partition(tmp_path):
    memory = MemoryConfig(file=tmp_path / "memory.json")
    memory.add("  ", ["a"])
    assert memory.get("") == {"a"}
    assert memory.get(MemoryConfig.DEFAULT_KEY) == {"a"}

