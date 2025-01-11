import QtQuick
import QtQuick.Controls
import QtQuick.Layouts


RowLayout {
  property string placeholder
  Label {
    text: placeholder
  }
  TextField {
    id: textfield
    Layout.fillWidth: true
    height: 100
    placeholderText: placeholder
    background: Rectangle {
      // color: textfield.focus ? "transparent" : "#353637"
      border.color: textfield.text.length ? "#4D82B2" : "#d9d9d9"
    }
  }
}
