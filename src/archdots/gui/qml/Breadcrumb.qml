import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
  property string text
  property string highlightColor
  property int horizontalPadding: 3
  property int verticalPadding: 3

  implicitWidth: breadcrumbText.implicitWidth + horizontalPadding
  implicitHeight: breadcrumbText.implicitHeight + verticalPadding

  border.color: highlightColor
  border.width: 1

  radius: height

  Text {
    id: breadcrumbText
    text: parent.text
    color: parent.highlightColor
    anchors.horizontalCenter: parent.horizontalCenter 
    anchors.verticalCenter: parent.verticalCenter 

    horizontalAlignment: Text.AlignHCenter
    verticalAlignment: Text.AlignVCenter
    elide: Text.ElideRight
  }


}

