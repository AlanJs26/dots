import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Button {
  id: control
  text: "Instalar"

  leftPadding: 10
  rightPadding: 10
  topPadding: 5
  bottomPadding: 5
  background: Rectangle {
    color: control.down ? "#2A6194" : "#4D82B2"
    radius: 5
  }
  contentItem: Text {
    text: control.text
    font: control.font
    color: "white"
    opacity: enabled ? 1.0 : 0.3
    horizontalAlignment: Text.AlignHCenter
    verticalAlignment: Text.AlignVCenter
    elide: Text.ElideRight
  }
}
