from pathlib import Path
import sys
import threading

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QObject, Slot

from archdots.constants import MODULE_PATH
from archdots.exceptions import GuiException
from archdots.gui.content_updaters import (
    update_package_panel,
    update_sidebar,
)


class Backend(QObject):
    window: QObject
    target_package: str = ""

    def __init__(self):
        super().__init__()

    @Slot()  # type: ignore
    def update_sidebar(self):
        if not self.window:
            return
        update_sidebar(self.window)

    @Slot()  # type: ignore
    def refresh_packages(self):
        if not self.window:
            return
        update_sidebar(self.window, use_memo=False)
        if self.target_package:
            self.update_package_panel(self.target_package)

    @Slot()  # type: ignore
    def update_package_panel(self):
        if not self.window:
            return
        update_package_panel(self.window)

    @Slot(QObject)  # type: ignore
    def startup(self, window: QObject):
        self.window = window
        thread = threading.Thread(target=self._startup)
        thread.start()

    def _startup(self):
        update_sidebar(self.window)
        update_package_panel(self.window)


def main_gui():
    app = QGuiApplication()
    engine = QQmlApplicationEngine()


    engine.addImportPath(Path(MODULE_PATH) / "src/archdots/gui")

    backend = Backend()
    engine.rootContext().setContextProperty('backend', backend)

    engine.loadFromModule("qml", "Main")
    if not engine.rootObjects():
        raise GuiException("Empty root objects")

    exit_code = app.exec()
    del engine
    sys.exit(exit_code)


if __name__ == "__main__":
    try:
        main_gui()
    except GuiException as e:
        print(e)
        sys.exit(-1)
