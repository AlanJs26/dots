import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Button {
  property int size: 25

  icon.color: down ? "#aa000000" : "#ff000000"
  icon.width: size
  icon.height: size
  width: size
  background: Rectangle {
    color: "transparent"
  }
}
