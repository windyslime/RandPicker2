import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import RinUI
FluentPage { title:qsTr("配置管理")
 FileDialog{id:save;fileMode:FileDialog.SaveFile;onAccepted:SettingsService.exportConfig(selectedFile)}
 FileDialog{id:open;fileMode:FileDialog.OpenFile;onAccepted:SettingsService.importConfig(selectedFile)}
 ColumnLayout{anchors.centerIn:parent;Button{text:qsTr("导出/备份配置");onClicked:save.open()}Button{text:qsTr("导入/恢复配置");onClicked:open.open()}Label{text:qsTr("配置包包含学生、小组和应用设置。")}}
}
