import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Window {
    width: 1000
    height: 800
    visible: true
    title: "archdots"

    RowLayout {
        anchors.fill:  parent
        spacing: 30

        SideBar {
          pendingPackages: 10
          unmanagedPackages: 10
        }

        PackagePanel {

        }

        Spacer {
          width: 0
        }

        
    }
}
