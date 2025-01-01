import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Window {
    width: 1000
    height: 800
    visible: true
    title: "archdots"

    property QtObject backend

    RowLayout {
        anchors.fill:  parent
        spacing: 30

        SideBar {
          pendingPackages: 10
          unmanagedPackages: 10
          backend_instance: backend
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
