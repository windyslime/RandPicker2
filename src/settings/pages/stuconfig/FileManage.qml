import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RinUI

FluentPage {
    title: qsTr("配置管理")
    ColumnLayout { anchors.centerIn: parent; Button { text: qsTr("保存学生配置"); onClicked: StudentsConfig.save_config() } Button { text: qsTr("保存小组配置"); onClicked: GroupsConfig.save_config() } Button { text: qsTr("重新加载配置"); onClicked: { StudentsConfig.reload_config(); GroupsConfig.reload_config() } } Label { text: qsTr("配置文件位于 config 目录，可直接复制进行备份。") } }
}
