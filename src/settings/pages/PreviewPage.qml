import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RinUI

FluentPage {
    title: qsTr("抽取预览")
    property var results: []
    RowLayout { Layout.fillWidth: true; Button { text: qsTr("抽人"); onClicked: results = ChoiceMaker.choosePeople(1, false) || [] } Button { text: qsTr("抽组"); onClicked: results = ChoiceMaker.advancedChoose(1, false) || [] } }
    ListView { Layout.fillWidth: true; Layout.fillHeight: true; model: results; delegate: Text { text: modelData.name || ""; font.pixelSize: 20; padding: 8 } }
}
