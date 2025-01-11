import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
  property int pendingPackages
  property int unmanagedPackages

  color: "#D9D9D9"
  width: 270
  Layout.fillHeight: true

  RowLayout {
    width: parent.width

    spacing: 10
    IconButton {
      size: 25
      Layout.alignment: Qt.AlignLeft
      icon.source: "../icons/refresh.png"
      onClicked: { 
        backend.refresh_packages()
      }
    }
    IconButton {
      size: 25
      Layout.alignment: Qt.AlignRight
      icon.source: "../icons/cog.png"
    }
  }

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
          objectName: "pendingPackagesNumber"
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
          objectName: "unmanagedPackagesNumber"
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

    // RowLayout {
    //   Layout.alignment: Qt.AlignHCenter
    //   spacing: 10
    // }
    StyledButton {
      Layout.alignment: Qt.AlignHCenter
      text: "Sincronizar"
    }

    Rectangle {
      Layout.preferredHeight: 10
    }

    ComboBox {
      objectName: "comboBox"
      id: comboBox
      Layout.fillWidth: true
      Layout.preferredHeight: 40
      Layout.alignment: Qt.AlignHCenter
      model: [ "Gerenciados", "Não Gerenciados", "Pendentes"]
      onActivated: { 
        backend.update_sidebar()
        backend.update_package_panel()
      }
    }

    ScrollView {
      clip: true
      Layout.fillWidth: true
      Layout.fillHeight: true
      ScrollBar.vertical.policy: listView.contentHeight > listView.height ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff

      ListView {
        objectName: "packagesList"
        id: listView
        focus: true

        property string currentName: listView.currentItem ? listView.currentItem.modelData.name : ''

        delegate: ItemDelegate {
          required property var modelData
          required property int index

          highlighted: ListView.isCurrentItem

          text: modelData.name
          width: listView.width

          onClicked: { 
            listView.currentIndex = index 
            listView.currentName = modelData.name
            backend.update_package_panel()
          }
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
