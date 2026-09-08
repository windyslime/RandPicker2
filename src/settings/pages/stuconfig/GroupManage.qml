import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RinUI
FluentPage {
 title: qsTr("小组管理"); property var groups: []; property var students: []
 function refresh(){groups=GroupsConfig.get_write_groups();students=StudentsConfig.get_write_students()}
 function toggle(g,id,c){var a=g.member_ids.slice(),i=a.indexOf(id);if(c&&i<0)a.push(id);if(!c&&i>=0)a.splice(i,1);GroupsConfig.set_members(g.id,a);refresh()}
 Component.onCompleted: refresh()
 ColumnLayout{anchors.fill:parent
  RowLayout{Button{text:qsTr("添加小组");onClicked:{GroupsConfig.add_group("新小组",1,true);refresh()}} Button{text:qsTr("保存");onClicked:GroupsConfig.save_config()} Button{text:qsTr("刷新");onClicked:refresh()}}
  ListView{Layout.fillWidth:true;Layout.fillHeight:true;model:groups;delegate:Frame{property var groupRef:modelData;width:ListView.view.width;ColumnLayout{width:parent.width
   RowLayout{TextField{Layout.fillWidth:true;text:modelData.name;onEditingFinished:GroupsConfig.update_group(modelData.id,text,modelData.weight,modelData.enabled)} SpinBox{from:0;to:100;value:modelData.weight;onValueModified:GroupsConfig.update_group(modelData.id,modelData.name,value,modelData.enabled)} CheckBox{text:qsTr("启用");checked:modelData.enabled;onToggled:GroupsConfig.update_group(modelData.id,modelData.name,modelData.weight,checked)} Button{text:qsTr("删除");onClicked:{GroupsConfig.remove_group(modelData.id);refresh()}}}
   Flow{Layout.fillWidth:true;Repeater{model:students;delegate:CheckBox{text:modelData.name;checked:groupRef.member_ids.indexOf(modelData.id)>=0;onToggled:toggle(groupRef,modelData.id,checked)}}}
  }}}
 }
}
