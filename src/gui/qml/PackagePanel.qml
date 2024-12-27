import QtQuick
import QtQuick.Controls
import QtQuick.Layouts


ColumnLayout {
  property string markdown_text
  property string pkgTitle
  property string pkgDescription
  property bool pkgManaged

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
    text: "dependencias"
    color: "#717171"
  }

  RowLayout {

    Repeater {
      objectName: "breadcrumbRepeater"
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
      text: "Instalar"
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
