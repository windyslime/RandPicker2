# 按学科记忆与本地持久化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 RandPicker 增加按 ClassIsland 当前科目隔离的个人抽选记忆、本地持久化，以及 ClassIsland 设置页的两个开关。

**Architecture:** 新增独立的 `MemoryConfig` 管理 `config/memory.json`，只保存学生 GUID 的科目分区。`ChoiceMaker` 在抽选前通过 `ClassIslandIntegration` 读取当前科目，并由两个 `SettingsConfig` 开关决定分区方式和是否跨进程加载/保存；IPC 失败时使用 `__default__`。QML 仅绑定设置开关，保留现有浮窗运行时记忆开关。

**Tech Stack:** Python 3.12+, PySide6, pythonnet/ClassIsland.Shared.IPC, RinUI QML, pytest。

## Global Constraints

- 个人抽选继续使用现有的 `ChoiceMaker.memoryEnabled` 运行时开关。
- 运行时关闭记忆只停止过滤和新增记录，不清除已有历史；`resetMemory()` 清除全部记忆并同步磁盘。
- 当前科目读取失败使用固定的 `__default__` 分区，不中断抽选。
- 记忆历史只保存学生 GUID；加载时过滤已不存在的学生 GUID。
- 不新增生产依赖；沿用现有配置目录和 PySide6/QML 模式。

---

### Task 1: MemoryConfig 本地存储

**Files:**
- Create: `core/config/memory.py`
- Modify: `core/config/__init__.py`
- Test: `tests/test_memory_config.py`

**Interfaces:**
- Produces `MemoryConfig(student_ids: Callable[[], Iterable[str]] | None = None, file: Path | None = None)`。
- Produces `get(subject_key: str) -> set[str]`、`add(subject_key: str, student_ids: Iterable[str]) -> None`、`clear(subject_key: str | None = None) -> None`、`reload() -> None`、`save() -> None`。
- Produces `MemoryConfig.DEFAULT_KEY = "__default__"` 和 `MemoryConfig.instance()`；默认实例使用 `CONFIG_DIR / "memory.json"`。

- [ ] **Step 1: Write the failing tests**

```python
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
```

- [ ] **Step 2: Run the focused tests and verify they fail**

Run: `python -m pytest tests/test_memory_config.py -q`

Expected: FAIL because `core.config.memory` does not exist.

- [ ] **Step 3: Implement the storage boundary**

Implement `MemoryConfig` with `{"subjects": {key: [guid, ...]}}` JSON, defensive parsing of non-dict/non-list data, atomic in-memory replacement on reload, parent directory creation on save, and `logger.exception`/empty fallback for malformed or unreadable files. Normalize keys to `__default__` when blank and intersect loaded IDs with the supplied student ID callback.

- [ ] **Step 4: Run the focused tests**

Run: `python -m pytest tests/test_memory_config.py -q`

Expected: PASS for round-trip filtering, per-subject clearing, malformed-file fallback, and missing-file creation.

- [ ] **Step 5: Commit**

```bash
git add core/config/memory.py core/config/__init__.py tests/test_memory_config.py
git commit -m "feat: add persistent subject memory storage"
```

### Task 2: Settings API and ClassIsland current subject

**Files:**
- Modify: `core/config/settings.py`
- Modify: `core/integration/classisland.py`
- Test: `tests/test_subject_lookup.py`

**Interfaces:**
- Produces `SettingsConfig.getCiMemoryBySubject() -> bool`, `setCiMemoryBySubject(bool) -> None`, `getCiMemoryPersistent() -> bool`, and `setCiMemoryPersistent(bool) -> None`.
- Produces `ClassIslandIntegration.get_current_subject() -> str | None`, returning a trimmed non-empty `Subject.Name` or `None`.

- [ ] **Step 1: Write the failing tests**

```python
def test_subject_lookup_returns_name(monkeypatch):
    integration = object.__new__(ClassIslandIntegration)
    integration.connectivity_status = "Connected"
    integration.ipcClient = FakeClient(FakeLessonsService(FakeSubject("语文")))
    assert integration.get_current_subject() == "语文"

def test_subject_lookup_failure_returns_none(monkeypatch):
    integration = object.__new__(ClassIslandIntegration)
    integration.connectivity_status = "NotConnected"
    assert integration.get_current_subject() is None
```

- [ ] **Step 2: Run focused tests and verify they fail**

Run: `python -m pytest tests/test_subject_lookup.py -q`

Expected: FAIL because the new settings methods and subject lookup are absent.

- [ ] **Step 3: Add default settings and getters/setters**

Add `memory_by_subject: True` and `memory_persistent: True` under the ClassIsland options in `DEFAULT_CONFIG`. Each getter reads a boolean with `True` fallback; each setter uses `setdefault("notification", {}).setdefault("options", {}).setdefault("classisland", {})`, writes the boolean, and calls `save_config()`.

- [ ] **Step 4: Add guarded IPC subject lookup**

Import `IPublicLessonsService` alongside the existing ClassIsland IPC types. In the available implementation, return `None` unless connectivity is `Connected` and `PeerProxy` exists; create a proxy with `GeneratedIpcFactory.CreateIpcProxy[IPublicLessonsService](self.ipcClient.Provider, self.ipcClient.PeerProxy)`, read `CurrentSubject`, read its `Name`, strip it, and catch/log all proxy and reflection errors. The unavailable implementation returns `None`.

- [ ] **Step 5: Run focused tests and compile check**

Run: `python -m pytest tests/test_subject_lookup.py -q` and `python -m py_compile core/config/settings.py core/integration/classisland.py`.

Expected: PASS on fakes and compile; on macOS where C# integration is unavailable, the fallback implementation remains importable.

- [ ] **Step 6: Commit**

```bash
git add core/config/settings.py core/integration/classisland.py tests/test_subject_lookup.py
git commit -m "feat: expose ClassIsland subject and memory settings"
```

### Task 3: ChoiceMaker subject-aware memory behavior

**Files:**
- Modify: `core/choice.py`
- Modify: `core/main.py`
- Test: `tests/test_choice_memory.py`

**Interfaces:**
- `ChoiceMaker` receives `MemoryConfig` and `ClassIslandIntegration` from existing singleton instances.
- Internal methods `_memory_key() -> str`, `_memory_subject_key() -> str`, and `_remember(subject_key, student_ids) -> None` keep selection code testable without changing QML-facing slots.

- [ ] **Step 1: Write behavior tests**

```python
def test_same_subject_remembers_after_runtime_toggle(fake_choice):
    fake_choice.subject = "语文"
    fake_choice.memoryEnabled = True
    first = fake_choice.choosePeople(1, False)
    fake_choice.memoryEnabled = False
    fake_choice.memoryEnabled = True
    second = fake_choice.choosePeople(1, False)
    assert first[0]["id"] != second[0]["id"]

def test_different_subjects_have_independent_history(fake_choice):
    fake_choice.memoryEnabled = True
    fake_choice.subject = "语文"
    chinese = fake_choice.choosePeople(1, False)[0]["id"]
    fake_choice.subject = "数学"
    assert fake_choice.memory.get("数学") == set()
    math = fake_choice.choosePeople(1, False)[0]["id"]
    assert fake_choice.memory.get("数学") == {math}
    assert fake_choice.memory.get("语文") == {chinese}
```

- [ ] **Step 2: Run focused tests and verify they fail**

Run: `python -m pytest tests/test_choice_memory.py -q`

Expected: FAIL because ChoiceMaker still has one `_memory_set` and no subject provider.

- [ ] **Step 3: Replace the single set with MemoryConfig-backed partitions**

Initialize `self.memoryConfig = MemoryConfig.instance()` and `self.classIsland = ClassIslandIntegration.instance()`. Use the settings getters to select a subject key or `MemoryConfig.DEFAULT_KEY`. Before filtering, read the partition into a mutable set; if all enabled students are remembered, clear only that partition and persist when enabled. After successful results, add IDs only when `memoryEnabled` is true, preserving the requested behavior that disabling the runtime toggle does not erase history. Persist immediately only when the local persistence setting is enabled. `resetMemory()` clears all partitions and saves only when persistence is enabled.

- [ ] **Step 4: Wire initialization order**

In `RPMain.init()`, instantiate `ClassIslandIntegration` before `ChoiceMaker` if needed so `ChoiceMaker` can retrieve its singleton, and instantiate `MemoryConfig` after `StudentsConfig` so its student-ID cleanup callback is valid. Keep existing notification startup and QML object exposure unchanged.

- [ ] **Step 5: Run behavior tests and compile check**

Run: `python -m pytest tests/test_choice_memory.py -q` and `python -m compileall core`.

Expected: PASS for same-subject restore, cross-subject isolation, global fallback, reset, and persistence toggles.

- [ ] **Step 6: Commit**

```bash
git add core/choice.py core/main.py tests/test_choice_memory.py
git commit -m "feat: partition picker memory by subject"
```

### Task 4: ClassIsland settings UI

**Files:**
- Modify: `src/settings/pages/settings/integrations/ClassIsland.qml`

**Interfaces:**
- Adds two independent `Switch` controls calling the four `SettingsConfig` methods from Task 2.

- [ ] **Step 1: Add the two setting cards**

Insert cards after “启用通知” and before “编辑通知格式”. Use `onToggled` so Loader initialization does not write settings accidentally:

```qml
SettingCard {
    Layout.fillWidth: true
    description: qsTr("启用后，不同学科分别记录已抽到的学生。")
    title: qsTr("按学科分开记忆")
    Switch {
        id: memoryBySubjectSwitch
        checked: SettingsConfig.getCiMemoryBySubject()
        onToggled: SettingsConfig.setCiMemoryBySubject(checked)
    }
}
SettingCard {
    Layout.fillWidth: true
    description: qsTr("启用后，记忆保存到本地；关闭记忆后再次启用仍会保留已抽选记录。")
    title: qsTr("记忆本地持久化")
    Switch {
        checked: SettingsConfig.getCiMemoryPersistent()
        onToggled: SettingsConfig.setCiMemoryPersistent(checked)
    }
}
```

- [ ] **Step 2: Run static QML/reference checks**

Run: `rg -n "getCiMemoryBySubject|getCiMemoryPersistent|setCiMemory" src/settings/pages/settings/integrations/ClassIsland.qml core/config/settings.py` and `python -m py_compile core/config/settings.py`.

Expected: both switches reference existing slots exactly once and the settings module compiles.

- [ ] **Step 3: Commit**

```bash
git add src/settings/pages/settings/integrations/ClassIsland.qml
git commit -m "feat: add subject memory settings to ClassIsland page"
```

### Task 5: End-to-end verification and review

**Files:**
- Modify: any files required by failing checks only.

- [ ] **Step 1: Run all focused tests**

Run: `python -m pytest tests -q`.

Expected: all memory, subject lookup, and choice behavior tests pass.

- [ ] **Step 2: Run project checks**

Run: `python -m compileall core` and `git diff --check`.

Expected: no Python compile errors and no whitespace errors.

- [ ] **Step 3: Review the final diff**

Run: `git diff origin/main...HEAD -- core src tests docs/superpowers` and verify that the only product changes are subject-aware personal memory, persistence, ClassIsland lookup, and the two settings controls.

- [ ] **Step 4: Commit any verification fixes**

```bash
git add core src tests
git commit -m "fix: address subject memory verification findings"
```
