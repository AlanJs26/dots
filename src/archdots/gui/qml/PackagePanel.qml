import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

SwipeView {
  id: view
  currentIndex: 0

  anchors.fill: parent

  property string markdown_text
  property string pkgTitle
  property string pkgDescription
  property bool pkgManaged
  property bool pkgInstalled

  ColumnLayout {
    property alias markdown_text: view.markdown_text
    property alias pkgTitle: view.pkgTitle
    property alias pkgDescription: view.pkgDescription
    property alias pkgManaged: view.pkgManaged
    property alias pkgInstalled: view.pkgInstalled

    id: packagePanel

    Layout.fillHeight: true
    Layout.fillWidth: true
    spacing: 0

    Label {
      text: pkgTitle
      font.pointSize: 44
    }
    Label {
      text: pkgDescription
      font.pointSize: 14
    }

    Spacer {}

    Label {
      text: breadcrumbRepeater.model.length ? "dependencias" : ''
      color: "#717171"
    }

    RowLayout {

      Repeater {
        objectName: "breadcrumbRepeater"
        id: breadcrumbRepeater
        // model: breadcrumbModel
        delegate: Breadcrumb {
          text: model.modelData.text
          highlightColor: model.modelData.installed ? "green" : "red"
          horizontalPadding: 20
          verticalPadding: 10
        }
      }

    }

    Spacer {}

    RowLayout {
      StyledButton {
        text: pkgInstalled ? "Desinstalar" : "Instalar"
        normalColor: pkgInstalled ? "#EB758E" : "#4D82B2"
        downColor: pkgInstalled ? "#A8203A" : "#2A6194"
      }
      CheckBox {
        id: managedCheckbox
        checked: pkgManaged
        text: "Gerenciado"
        Binding { packagePanel.pkgManaged: managedCheckbox.checked }
      }
      Spacer {
        Layout.fillWidth: true
      }
      StyledButton {
        text: "Editar"
        onClicked: view.currentIndex = (view.currentIndex + 1) % 2
      }
    }

    Spacer {}

    MenuSeparator {
      Layout.fillWidth: true
    }

    Spacer {}

    ScrollView {
      clip: true
      Layout.fillWidth: true
      Layout.fillHeight: true

      Text {
        Layout.fillHeight: true
        Layout.fillWidth: true
        textFormat: TextEdit.MarkdownText
        text: markdown_text
      }
    }
  }


  ColumnLayout {
    Rectangle {
      Layout.fillHeight: true
      Layout.fillWidth: true
      color: 'green'
    }
  }

}
