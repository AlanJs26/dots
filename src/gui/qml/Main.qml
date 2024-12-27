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

        PackagePanel {
          id: packagePanel
          objectName: "packagePanel"
          pkgTitle: "Tabbed"
          pkgDescription: "simple generic tabbed fontend to xembed-aware applications"
          markdown_text: "## README"
          // pkgManaged: false
        }

        Spacer {
          width: 0
        }

        
    }
}
