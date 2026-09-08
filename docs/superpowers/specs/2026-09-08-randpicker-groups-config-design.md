# RandPicker 抽组与配置管理设计

## 目标
补齐抽组、小组管理、配置管理、抽取预览，并将浮窗按钮文案改为“抽人”“抽组”。

## 数据模型
新增 `config/groups.json`，结构为 `{ "groups": [{"id","name","weight","enabled","member_ids":[]}] }`。`GroupsConfig` 采用与 `StudentsConfig` 相同的读写缓冲和快照机制，提供分组增删改查、成员分配、权重和启用状态管理，并在读取时清理不存在的学生引用。

## 抽取流程
`ChoiceMaker.advancedChoose(number, notify)` 从启用小组中按权重进行不重复抽样，结果为带 id/name/weight/member_ids 的组对象；通知使用 `pick_type="group"`，以组名作为 names。无可用组时返回空结果并记录日志。

## UI
`GroupManage.qml` 提供增删改、权重、启用状态和学生复选框成员分配，并支持刷新/保存。`FileManage.qml` 提供 students/groups/settings 的导入、导出、备份和恢复。新增 `PreviewPage.qml`，展示最近一次抽人或抽组结果并提供数量控制。浮窗按钮文案更新为“抽人”“抽组”，组按钮调用抽组接口。

## 通知与验证
Native 和 ClassIsland 均使用统一 names 模板发送组名；ClassIsland 组通知填充组对象名称。配置损坏时回退默认配置并发送原有错误通知。验证包括 Python 配置/抽取测试、QML 文件与导航引用检查，以及项目可运行性检查。
