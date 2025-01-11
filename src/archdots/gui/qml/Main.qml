import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Window {
    width: 1000
    height: 800
    visible: true
    title: "archdots"

    id: main

    RowLayout {
        Component.onCompleted: backend.startup(main);

        anchors.fill:  parent
        spacing: 30

        SideBar {
          pendingPackages: 10
          unmanagedPackages: 10
        }

        Rectangle {
          clip: true
          Layout.fillHeight: true
          Layout.fillWidth: true

          PackagePanel {
            id: packagePanel
            objectName: "packagePanel"
            pkgTitle: ""
            pkgDescription: ""
            markdown_text: ""
            pkgManaged: false
          }
        }

        Spacer {
          width: 0
        }

        
    }
}
