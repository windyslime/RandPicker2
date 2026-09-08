# RandPicker 抽组与配置管理 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 完成小组数据管理、抽组算法、管理页面、配置导入导出、抽取预览和按钮文案。

**Architecture:** 新增独立 groups.json 与 GroupsConfig，沿用 StudentsConfig 的读写缓冲；ChoiceMaker 通过 GroupsConfig 抽取组对象并复用通知接口；QML 页面直接调用配置对象的 Slot。

**Tech Stack:** Python 3.12+, PySide6, QML/RinUI, pytest。

## Global Constraints

- 组对象字段固定为 id/name/weight/enabled/member_ids。
- 抽组按启用组权重不重复抽样，结果为组名对象。
- 页面修改写入缓冲，保存时持久化。

### Task 1: GroupsConfig
**Files:** Create `core/config/groups.py`; Modify `core/config/__init__.py` if needed; Test via Python smoke script.
- [ ] 实现加载、默认配置、ID 补全、保存/重载、未保存检测。
- [ ] 实现 `get_groups/get_enabled_groups/get_single_group/get_write_groups/add_group/remove_group/update_group/set_members`。
- [ ] 学生删除后抽取时过滤无效 member_ids。
- [ ] 运行 `python -m py_compile core/config/groups.py`。

### Task 2: ChoiceMaker 与通知
**Files:** Modify `core/choice.py`, `core/integration/classisland.py`, `src/widget.qml`.
- [ ] 注入 GroupsConfig。
- [ ] 实现 `advancedChoose(number=1, notify=True)`，按权重不重复抽取，返回完整组对象；通知时传组对象。
- [ ] ClassIsland 组通知填充组名字段可用的结构，避免 pass。
- [ ] 按钮文案改为“抽人”“抽组”，调用真实 Slot。
- [ ] 运行 Python 编译检查与最小抽取脚本。

### Task 3: QML 管理和预览页面
**Files:** Create `src/settings/pages/stuconfig/GroupManage.qml`, `src/settings/pages/stuconfig/FileManage.qml`, `src/settings/pages/PreviewPage.qml`.
- [ ] 小组页面实现列表、添加/删除、名称/权重/启用编辑、学生复选框、保存/刷新。
- [ ] 配置页面实现导入、导出、备份、恢复，使用文件对话框和 Python 配置服务。
- [ ] 预览页面实现数量控制、抽人/抽组按钮和结果列表。
- [ ] 确认 `src/settings/main.qml` 导航引用全部存在。

### Task 4: 配置服务与验证
**Files:** Modify `core/config/students.py` or add `core/config/files.py`; QML pages as needed.
- [ ] 提供统一配置导入导出/备份恢复 Slot，覆盖 students/groups/settings。
- [ ] 对 JSON 做字典结构校验，失败时保留当前配置并发送 native 错误通知。
- [ ] 运行 `python -m compileall core` 与项目测试/静态检查。
- [ ] 提交功能变更。
