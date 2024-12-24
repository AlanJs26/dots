import sys

from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickView
from PySide6.QtQml import QQmlApplicationEngine

from src.constants import MODULE_PATH
from pathlib import Path


class GuiException(Exception):
    pass


def main_gui():
    app = QGuiApplication()
    engine = QQmlApplicationEngine()
    engine.addImportPath(Path(MODULE_PATH) / "src/gui")
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
