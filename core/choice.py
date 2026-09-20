"""
随机选择
"""
from typing import Any
from random import choices

from PySide6.QtCore import QObject, Slot, Signal, Property
from loguru import logger

from .config.students import StudentsConfig
from .config.groups import GroupsConfig
from .config.memory import MemoryConfig
from .config.settings import SettingsConfig
from .integration.classisland import ClassIslandIntegration
from .integration import NotificationManager


class ChoiceMaker(QObject):
    _instance: "ChoiceMaker" = None

    # 记忆模式和变化信号
    memoryEnabledChanged = Signal(bool)

    @classmethod
    def instance(cls) -> "ChoiceMaker":
        return cls._instance

    def __init__(self, parent=None):
        super().__init__()
        ChoiceMaker._instance = self
        self.studentsConfig = StudentsConfig.instance()
        self.groupsConfig = GroupsConfig.instance()
        self.notificationManager = NotificationManager.instance()
        self.settingsConfig = SettingsConfig.instance()
        self.classIsland = ClassIslandIntegration.instance()
        self.memoryConfig = MemoryConfig(
            student_ids=lambda: [
                student.get("id")
                for student in self.studentsConfig.get_students()
                if isinstance(student, dict)
            ]
        )
        if not self.settingsConfig.getCiMemoryPersistent():
            # Ignore persisted history for this session without deleting it.
            self.memoryConfig.clear()
        self._refresh()

        # 记忆模式状态
        self._memory_enabled = False
        # 记忆历史由 MemoryConfig 按科目分区管理。

    def _refresh(self):
        self.students = self.studentsConfig.get_enabled_students()
        self.students_weights = self.studentsConfig.get_partof_students_weights(self.students)

    @Slot(int, bool, result=list)
    def choosePeople(self, number: int = 1, notify: bool = True) -> list[Any] | None:
        """随机选择学生"""
        self._refresh()
        if len(self.students) == 0:
            logger.warning("没有可用的学生进行选择。")
            return None

        memory_key = self._memory_key()

        # 记忆模式前处理
        available_students = list(self.students)
        available_weights = list(self.students_weights)
        if self._memory_enabled:
            remembered = self.memoryConfig.get(memory_key)
            pairs = [(s, w) for s, w in zip(available_students, available_weights) if s not in remembered]
            if not pairs:
                # 只清空当前科目分区，允许该科目开始下一轮抽选。
                self.memoryConfig.clear(memory_key)
                self._save_memory()
            else:
                available_students, available_weights = map(list, zip(*pairs))

        if number > len(available_students):
            number = len(available_students)

        # 不重复抽样
        result = []
        temp_students = list(available_students)
        temp_weights = list(available_weights)
        for _ in range(number):
            pick = choices(temp_students, weights=temp_weights, k=1)[0]
            result.append(pick)
            idx = temp_students.index(pick)
            temp_students.pop(idx)
            temp_weights.pop(idx)
        logger.info(f"选择结果: {result}")

        # 发送通知
        if notify:
            self.notificationManager.send(
                # title=f"抽选了 {number} 名学生",
                pick_type="person",
                # message=", ".join([self.studentsConfig.get_single_student(s).get("name", "未知") for s in result])
                stus=[self.studentsConfig.get_single_student(s) for s in result]
            )
            self._remember(memory_key, result)
            return None
        else:
            final_result = []
            for student_id in result:
                student = self.studentsConfig.get_single_student(student_id).copy()
                student["properties"] = self.studentsConfig.getProperty(student_id)
                student["avatar"] = self.studentsConfig.getAvatarPath(student_id)
                final_result.append(student)
            self._remember(memory_key, result)
            return final_result

    @Slot(int, bool, result=list)
    def advancedChoose(self, number: int = 1, notify: bool = True) -> list[Any]:
        groups = self.groupsConfig.get_enabled_groups()
        if not groups: return []
        number = min(max(1, number), len(groups)); pool = list(groups); result = []
        for _ in range(number):
            pick = choices(pool, weights=[g.get("weight", 1) for g in pool], k=1)[0]; result.append(pick); pool.remove(pick)
        if notify: self.notificationManager.send("group", result); return []
        return result

    @Property(bool, notify=memoryEnabledChanged)
    def memoryEnabled(self) -> bool:
        """获取当前会话内记忆模式状态"""
        return getattr(self, "_memory_enabled", False)

    @memoryEnabled.setter
    def memoryEnabled(self, enabled: bool) -> None:
        """启用/禁用记忆过滤（不会清除已有历史）。"""
        self._memory_enabled = bool(enabled)
        try:
            self.memoryEnabledChanged.emit(self._memory_enabled)
        except Exception:
            pass

    @Slot()
    def resetMemory(self) -> None:
        """清除全部科目记忆，并同步清空本地文件。"""
        self.memoryConfig.clear()
        self.memoryConfig.save()

    def _memory_key(self) -> str:
        """根据 ClassIsland 当前科目计算本次抽选的记忆分区。"""
        if not self.settingsConfig.getCiMemoryBySubject():
            return MemoryConfig.DEFAULT_KEY
        try:
            subject = self.classIsland.get_current_subject() if self.classIsland else None
        except Exception as e:
            logger.debug(f"获取当前科目失败，使用默认记忆分区: {e}")
            subject = None
        return MemoryConfig._normalize_key(subject)

    def _save_memory(self) -> None:
        if self.settingsConfig.getCiMemoryPersistent():
            self.memoryConfig.save()

    def _remember(self, memory_key: str, student_ids: list[str]) -> None:
        if not self._memory_enabled or not student_ids:
            return
        self.memoryConfig.add(memory_key, student_ids)
        self._save_memory()
