import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {

  property int pendingPackages
  property int unmanagedPackages

  color: "#D9D9D9"
  width: 270
  Layout.fillHeight: true
  ColumnLayout {
    width: parent.width
    height: parent.height
    spacing: 0

    RowLayout {
      Layout.alignment: Qt.AlignHCenter
      Layout.minimumHeight: 100
      spacing: 20
      ColumnLayout {
        spacing: 0
        Text {
          text: pendingPackages
          Layout.alignment: Qt.AlignHCenter
          font.pointSize: 32
        }
        Text {
          text: "Pendentes"
          Layout.alignment: Qt.AlignHCenter
        }
      }
      ColumnLayout {
        spacing: 0
        Text {
          text: unmanagedPackages
          Layout.alignment: Qt.AlignHCenter
          font.pointSize: 32
        }
        Text {
          text: "Não Gerenciados"
          Layout.alignment: Qt.AlignHCenter
        }
      }
    }

    RowLayout {
      Layout.alignment: Qt.AlignHCenter
      spacing: 10
      Text {
        text: "C"
      }
      StyledButton {
        text: "Instalar Pendentes"
      }
    }

    Rectangle {
      Layout.preferredHeight: 10
    }

    ComboBox {
      Layout.fillWidth: true
      Layout.preferredHeight: 40
      Layout.alignment: Qt.AlignHCenter
      model: [ "Gerenciados", "Não Gerenciados", "Pendentes"]
    }

    ScrollView {
      clip: true
      Layout.fillWidth: true
      Layout.fillHeight: true
      ScrollBar.vertical.policy: ScrollBar.AlwaysOn

      ListView {
        model: 80
        delegate: ItemDelegate {
          text: "Item " + index

          required property int index
        }
      }

    }

    Button {
      Layout.fillWidth: true
      Layout.minimumHeight: 40
      text: "Novo Pacote"
    }



  }
}
