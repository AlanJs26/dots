import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.qmlmodels

SwipeView {
  id: view
  currentIndex: 1

  anchors.fill: parent

  property string markdown_text
  property string pkgTitle
  property string pkgDescription
  property bool pkgManaged
  property bool pkgInstalled



  ColumnLayout {
    // Rectangle {
    //   Layout.fillHeight: true
    //   Layout.fillWidth: true
    //   color: 'green'
    // }
    RowLayout {
      IconButton {
        size: 25
        Layout.alignment: Qt.AlignLeft
        icon.source: "../icons/refresh.png"
      }

      Label {
        text: 'Pacote Personalizado'
        font.pointSize: 34
      }
    }
    Field { placeholder: "Nome" }
    Field { placeholder: "Descrição" }
    Field { placeholder: "Url" }

    Label {text: 'Arquivos Externos'}

    RowLayout {
      TextField {
        implicitWidth: 300
        placeholderText: 'Digite Aqui...'
      }
      StyledButton {
        text: 'Adicionar'
      }
    }

    CustomTable {
      columnNames: ['Url', 'action']
      rows: [
        { "Url": "teste" },
        { "Url": "teste" }
      ]
      TableModelColumn { display: "Url" }
      TableModelColumn { display: "action" }
      Layout.fillWidth: true
    }

    Label {text: 'Dependências'}

    RowLayout {
      ComboBox {
        Layout.preferredWidth: 100
        Layout.preferredHeight: 30
        model: [ "winget", "pacman", "custom"]
      }
      TextField {
        implicitWidth: 300
        placeholderText: 'Digite Aqui...'
      }
      StyledButton {
        text: 'Adicionar'
      }
    }

    CustomTable {
      columnNames: ['Fonte', 'Nome', 'action']
      rows: [
        { "Fonte": "teste", 'Nome': 'libx11' },
        { "Fonte": "custom", 'Nome': 'tabbed' },
      ]
      TableModelColumn { display: "Fonte" }
      TableModelColumn { display: "Nome" }
      TableModelColumn { display: "action" }
      Layout.fillWidth: true
    }

    RowLayout {
      Label { text: 'Tipo de Pacote' }
      ComboBox {
        Layout.preferredWidth: 100
        Layout.preferredHeight: 30
        model: [ "winget", "pacman", "custom"]
      }
    }


    Spacer {
      Layout.fillHeight: true
    }
  }


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


}
