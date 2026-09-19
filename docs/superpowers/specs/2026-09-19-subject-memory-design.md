# RandPicker 按学科记忆与本地持久化设计

## 目标

让 RandPicker 的个人抽选记忆能够按 ClassIsland 当前科目分开保存，并在本地持久化。用户在语文课抽选过学生后，即使暂时关闭浮窗中的“记忆”，再次启用语文课记忆时仍排除此前抽过的学生；切换到数学课后使用独立的记忆分区。

## 范围与行为

- 个人抽选继续使用现有的 `ChoiceMaker.memoryEnabled` 运行时开关。
- 运行时关闭记忆只停止过滤和新增记录，不清除已有历史；`resetMemory()` 清除全部记忆并同步磁盘。
- “按学科分开记忆”开启时，记忆键为当前 ClassIsland 科目名称；关闭时所有科目共用一个全局键，保持旧版单集合语义。
- “记忆本地持久化”开启时，记忆历史保存到 `config/memory.json` 并在启动时加载；关闭时只在当前进程保存，重启后清空运行时历史。
- 当前科目通过 ClassIsland v2 的 `IPublicLessonsService.CurrentSubject` 读取。连接不可用、课表未加载、当前科目为空或 IPC 调用失败时，使用固定的 `__default__` 分区，不中断抽选。
- 记忆历史只保存学生 GUID，不保存姓名、权重等可变资料。加载时过滤已不存在的学生 GUID。
- 某个记忆分区的可用学生耗尽时，只清空该分区并开始下一轮，不影响其他科目。

两个 ClassIsland 设置开关默认开启，使新安装用户直接获得按科目、本地持久化的行为；旧配置缺少字段时由默认配置补全。关闭开关后保留已有文件，重新开启即可恢复历史。

## 架构

新增 `core/config/memory.py`，负责独立的 `memory.json` 文件、读写、格式校验和学生 GUID 清理。数据结构为：

```json
{
  "subjects": {
    "语文": ["student-guid-1", "student-guid-2"],
    "__default__": []
  }
}
```

`ChoiceMaker` 注入 `MemoryConfig` 和 `ClassIslandIntegration`。每次 `choosePeople()` 在刷新学生列表后获取当前记忆键，按当前设置决定使用科目键或全局键；启用运行时记忆时过滤对应 GUID，并在抽选成功后更新内存。持久化开关开启时更新后立即保存，关闭时不读写文件但仍维护本次进程内的分区集合。

`ClassIslandIntegration` 增加只读的当前科目方法，使用与现有 `IRPService` 相同的 IPC provider/peer 创建 `IPublicLessonsService` proxy。所有反向读取均在异常边界内完成，返回空值时由 `ChoiceMaker` 使用 `__default__`。

`SettingsConfig` 在 `notification.options.classisland` 下新增 `memory_by_subject` 和 `memory_persistent` 两个布尔字段及对应 getter/setter。`ClassIsland.qml` 在通知启用设置附近增加两个 `SettingCard`，只负责读写这两个配置，不改变浮窗上的运行时记忆开关。

## 数据流

1. 用户点击抽选，`ChoiceMaker` 刷新启用学生列表。
2. 若按学科开关开启，ChoiceMaker 从 ClassIsland 读取当前科目名称；读取失败使用 `__default__`。
3. 若运行时记忆开启，ChoiceMaker 从对应分区排除历史 GUID；池耗尽时清空该分区并重新抽取。
4. 抽选成功后，将本次 GUID 写入对应分区；若本地持久化开启则保存 `memory.json`。
5. 关闭运行时记忆或关闭两个设置开关时不主动删除历史；重置按钮删除全部分区并保存空结构。

## 兼容性与错误处理

- `memory.json` 不存在时创建空结构；JSON 损坏或结构不正确时记录错误并从空结构开始，不影响学生配置和应用启动。
- 旧版没有新增设置字段时使用默认值；已有学生删除后不会继续占用记忆名额。
- ClassIsland 不可用时不改变通知回退逻辑，当前科目直接使用默认分区。
- 学科名称为空、空白或无法转换为字符串时统一使用 `__default__`；名称前后空白会被去除。

## 验证

新增针对核心行为的 Python 测试或最小可重复脚本，覆盖：同一科目在关闭再开启运行时记忆后仍排除历史、不同科目互不影响、按学科开关关闭时全局共享、持久化开关跨实例恢复、禁用持久化时重启不恢复、无效学生 GUID 被清理、IPC 读取失败回退默认分区。另行运行 `python -m compileall core`，并检查 QML 设置页和现有项目启动路径。
