import QtQuick
import QtQuick.Controls
import QtQuick.Layouts


ColumnLayout {
  Layout.fillHeight: true
  Layout.fillWidth: true
  spacing: 0

  Label {
    text: "Tabbed"
    font.pointSize: 44
  }
  Label {
    text: "simple generic tabbed fontend to xembed-aware applications"
    font.pointSize: 14
  }

  Spacer {}

  Label {
    text: "dependencias"
    color: "#717171"
  }
  RowLayout {
    Breadcrumb {
      text: "libx11"
      highlightColor: "green"
      horizontalPadding: 20
      verticalPadding: 10
    }
    Breadcrumb {
      text: "rust"
      highlightColor: "red"
      horizontalPadding: 20
      verticalPadding: 10
    }
    Breadcrumb {
      text: "gcc"
      highlightColor: "green"
      horizontalPadding: 20
      verticalPadding: 10
    }
  }

  Spacer {}

  RowLayout {
    StyledButton {
      text: "Instalar"
    }
    CheckBox {
      text: "Gerenciado"
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


  Rectangle {
    // color: ""
    Layout.fillHeight: true
    Layout.fillWidth: true
  }
}
