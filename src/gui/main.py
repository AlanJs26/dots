from functools import reduce
import sys

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QObject, Slot

from src.package_manager import Custom, PackageManager, check_packages, package_managers
from src.package import Package
from src.constants import MODULE_PATH
from src.package_utils import (
    get_managed_packages,
    get_pending_packages,
    get_unmanaged_packages,
)
from pathlib import Path


class GuiException(Exception):
    pass


def findChild(root: QObject, objectName: str) -> QObject:
    child: QObject | None = root.findChild(QObject, objectName)
    if not child:
        raise GuiException(f'Could not find element named "{objectName}"')
    return child


def update_package_panel(target_package: str, window: QObject):
    pkg_name, pm_name = target_package.rsplit(" - ")

    if pm_name == "custom":
        custom_packages: list[Package] = Custom().get_packages()
        pkg = next(filter(lambda pkg: pkg.name == pkg_name, custom_packages), None)
        if not pkg:
            raise GuiException(f'Could not find package named "{pkg_name}"')

        data = [
            {"text": dep_name, "installed": status}
            for dep_name, status in check_packages(pkg.depends).items()
        ]

        breadcrumbs = findChild(window, "breadcrumbRepeater")

        breadcrumbs.setProperty("model", data)

        packagePanel = findChild(window, "packagePanel")

        packagePanel.setProperty("pkgTitle", pkg.name)
        packagePanel.setProperty("pkgDescription", pkg.description)

        markdown_text = ""
        readme_path = Path(pkg.pkgbuild).parent / "README.md"
        if readme_path.is_file():
            with open(readme_path, "r") as f:
                markdown_text = f.read()

        packagePanel.setProperty("markdown_text", markdown_text)

    else:
        breadcrumbs = findChild(window, "breadcrumbRepeater")

        breadcrumbs.setProperty("model", [])

        packagePanel = findChild(window, "packagePanel")

        packagePanel.setProperty("pkgTitle", pkg_name)
        packagePanel.setProperty("pkgDescription", "")
        packagePanel.setProperty("markdown_text", "")


def update_packages_list(window: QObject, use_memo=True):
    combo_box = findChild(window, "comboBox")
    packages_list = findChild(window, "packagesList")

    combo_index = combo_box.property("currentIndex")

    filtered_packages: dict[PackageManager, list[str]] = {}
    match combo_index:
        case 0:
            filtered_packages = get_managed_packages(use_memo)
        case 1:
            filtered_packages = get_unmanaged_packages(use_memo)
        case 2:
            filtered_packages = get_pending_packages(use_memo)

    data = []
    for pm, pkgs in filtered_packages.items():
        data.extend({"name": f"{pkg_name} - {pm.name}"} for pkg_name in pkgs)

    packages_list.setProperty("model", data)


def update_sidebar(window: QObject, use_memo=True):
    update_packages_list(window, use_memo)
    pending_packages_number = findChild(window, "pendingPackagesNumber")
    unmanaged_packages_number = findChild(window, "unmanagedPackagesNumber")

    pending_packages_number.setProperty(
        "text",
        reduce(lambda p, n: p + len(n), get_pending_packages(use_memo).values(), 0),
    )
    unmanaged_packages_number.setProperty(
        "text",
        reduce(lambda p, n: p + len(n), get_unmanaged_packages(use_memo).values(), 0),
    )


class Backend(QObject):
    window: QObject
    target_package: str = ""

    def __init__(self, window: QObject):
        super().__init__()
        self.window = window

    @Slot()  # type: ignore
    def update_sidebar(self):
        update_sidebar(self.window)

    @Slot()  # type: ignore
    def refresh_packages(self):
        update_sidebar(self.window, use_memo=False)
        if self.target_package:
            self.update_package_panel(self.target_package)

    @Slot(str)  # type: ignore
    def update_package_panel(self, target_package: str):
        update_package_panel(target_package, self.window)
        self.target_package = target_package


def main_gui():
    app = QGuiApplication()
    engine = QQmlApplicationEngine()
    engine.addImportPath(Path(MODULE_PATH) / "src/gui")
    engine.loadFromModule("qml", "Main")
    if not engine.rootObjects():
        raise GuiException("Empty root objects")

    window = engine.rootObjects()[0]
    backend = Backend(window)

    update_sidebar(window)

    window.setProperty("backend", backend)

    exit_code = app.exec()
    del engine
    sys.exit(exit_code)


if __name__ == "__main__":
    try:
        main_gui()
    except GuiException as e:
        print(e)
        sys.exit(-1)
