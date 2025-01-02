from functools import reduce
from pathlib import Path

from PySide6.QtCore import QObject

from archdots.package_manager import Custom, PackageManager, check_packages
from archdots.exceptions import GuiException
from archdots.package import Package
from archdots.package_utils import (
    get_managed_packages,
    get_pending_packages,
    get_unmanaged_packages,
)


def findChild(root: QObject, objectName: str) -> QObject:
    child: QObject | None = root.findChild(QObject, objectName)
    if not child:
        raise GuiException(f'Could not find element named "{objectName}"')
    return child


def update_package_panel(window: QObject, use_memo=True):
    packages_list = findChild(window, "packagesList")
    packagePanel = findChild(window, "packagePanel")
    breadcrumbs = findChild(window, "breadcrumbRepeater")

    breadcrumbs_data = []
    pkg_description = ""
    markdown_text = ""
    pkg_managed = True
    pkg_installed = True

    current_item_name = packages_list.property("currentName")
    if not current_item_name:
        packagePanel.setProperty("pkgInstalled", pkg_installed)
        packagePanel.setProperty("pkgManaged", pkg_managed)
        packagePanel.setProperty("markdown_text", markdown_text)
        packagePanel.setProperty("pkgDescription", pkg_description)
        breadcrumbs.setProperty("model", breadcrumbs_data)
        packagePanel.setProperty("pkgTitle", "")
        return

    pkg_name, pm_name = current_item_name.rsplit(" - ")

    if pm_name == "custom":
        custom_packages: list[Package] = Custom().get_packages()
        pkg = next(filter(lambda pkg: pkg.name == pkg_name, custom_packages), None)
        if not pkg:
            raise GuiException(f'Could not find package named "{pkg_name}"')

        breadcrumbs_data = [
            {"text": dep_name, "installed": status}
            for dep_name, status in check_packages(pkg.depends).items()
        ]

        readme_path = Path(pkg.pkgbuild).parent / "README.md"
        if readme_path.is_file():
            with open(readme_path, "r") as f:
                markdown_text = f.read()

            pkg_description = pkg.description

    unmanaged_by_pmname = {
        pm.name: pkgs for pm, pkgs in get_unmanaged_packages(use_memo).items()
    }
    pending_by_pmname = {
        pm.name: pkgs for pm, pkgs in get_pending_packages(use_memo).items()
    }

    if pm_name in unmanaged_by_pmname and pkg_name in unmanaged_by_pmname[pm_name]:
        pkg_managed = False
    if pm_name in pending_by_pmname and pkg_name in pending_by_pmname[pm_name]:
        pkg_installed = False

    packagePanel.setProperty("pkgInstalled", pkg_installed)
    packagePanel.setProperty("pkgManaged", pkg_managed)
    packagePanel.setProperty("markdown_text", markdown_text)
    packagePanel.setProperty("pkgDescription", pkg_description)
    breadcrumbs.setProperty("model", breadcrumbs_data)
    packagePanel.setProperty("pkgTitle", pkg_name)


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
