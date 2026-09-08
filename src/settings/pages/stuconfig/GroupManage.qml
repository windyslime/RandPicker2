import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RinUI

FluentPage {
    title: qsTr("小组管理"); property var groups: []
    function refresh() { groups = GroupsConfig.get_write_groups() }
    Component.onCompleted: refresh()
    ColumnLayout { Layout.fillWidth: true; Layout.fillHeight: true
        RowLayout { Button { text: qsTr("添加小组"); onClicked: { GroupsConfig.add_group("新小组", 1, true); refresh() } } Button { text: qsTr("保存"); onClicked: GroupsConfig.save_config() } Button { text: qsTr("刷新"); onClicked: refresh() } }
        ListView { Layout.fillWidth: true; Layout.fillHeight: true; model: groups; delegate: RowLayout { width: parent.width; TextField { text: modelData.name; onEditingFinished: GroupsConfig.update_group(modelData.id, text, modelData.weight, modelData.enabled) } SpinBox { from: 0; to: 100; value: modelData.weight; onValueModified: GroupsConfig.update_group(modelData.id, modelData.name, value, modelData.enabled) } CheckBox { checked: modelData.enabled; onToggled: GroupsConfig.update_group(modelData.id, modelData.name, modelData.weight, checked) } Button { text: qsTr("删除"); onClicked: { GroupsConfig.remove_group(modelData.id); refresh() } } } }
    }
}
