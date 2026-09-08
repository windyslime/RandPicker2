import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RinUI
FluentPage{title:qsTr("抽取预览");property var results:[];property int count:1
 ColumnLayout{anchors.fill:parent;RowLayout{Button{text:"−";onClicked:count=Math.max(1,count-1)}Label{text:qsTr("数量：")+count}Button{text:"+";onClicked:count=Math.min(99,count+1)}Button{text:qsTr("抽人");onClicked:results=ChoiceMaker.choosePeople(count,false)||[]}Button{text:qsTr("抽组");onClicked:results=ChoiceMaker.advancedChoose(count,false)||[]}}ListView{Layout.fillWidth:true;Layout.fillHeight:true;model:results;delegate:Label{text:modelData.name||"";font.pixelSize:22;padding:10}}}
}
