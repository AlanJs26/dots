import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.qmlmodels

Rectangle {
  id: customTable
  // height: horizontalHeader.height + tableView.height
  width: 500
  property var columnNames
  property var rows
  default property alias data: tableModel.columns

  HorizontalHeaderView {
    id: horizontalHeader
    anchors.left: tableView.left
    anchors.top: parent.top
    syncView: tableView
    clip: true

    model: columnNames

    delegate: Rectangle {
      implicitWidth: 100
      implicitHeight: 30
      color: modelData == 'action' ? 'transparent' : "lightgray"

      Text {
        text: modelData == 'action' ? '' : modelData
        anchors.centerIn: parent
        font.bold: true
      }
    }

  }

  TableView {
    id: tableView

    anchors.left: horizontalHeader.left
    anchors.top: horizontalHeader.bottom
    anchors.right: parent.right
    anchors.bottom: parent.bottom
    clip: true

    model: TableModel {
      id: tableModel
      columns: columns
    }

    delegate: Rectangle {
      id: tableItem
      implicitWidth: model.display == undefined ? 25 : 100
      implicitHeight: 25
      color: model.display == undefined ? 'transparent' : "lightgray"

      Text {
        text: model.display ?? ''
        anchors.centerIn: parent
        visible: model.display ?? false
      }
      IconButton {
        size: 25
        anchors.centerIn: parent
        icon.source: "../icons/cog.png"
        visible: model.display == undefined
      }
    }

  }

  Component.onCompleted: {
    tableModel.clear()
    tableModel.rows = rows
    customTable.implicitHeight = 30 + rows.length * 25
  }
}
