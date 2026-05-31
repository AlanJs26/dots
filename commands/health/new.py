"""
ARCHDOTS
help: create a new health script
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

from archdots.ui.console import print_title
from archdots.packages.package import Package
from archdots.packages.dependencies import are_custom_packages_valid
from archdots.packages.managers import Custom
from archdots.packages.managers.registry import get_package_managers
from archdots.utils.editors import default_editor
from archdots.utils.templates import generate_pkgbuild_template
from rich import print
from rich.prompt import Prompt, Confirm
from archdots.core.constants import HEALTH_FOLDER, PLATFORM
from archdots.core.platforms.registry import get_all_platforms
from pathlib import Path

import os

valid_platforms = [p.name for p in get_all_platforms()]
if any(
    Path(HEALTH_FOLDER).joinpath(d).is_dir()
    for d in valid_platforms
    if Path(HEALTH_FOLDER).exists()
):
    effective_health_folder = Path(HEALTH_FOLDER) / PLATFORM
else:
    effective_health_folder = Path(HEALTH_FOLDER)

os.makedirs(effective_health_folder, exist_ok=True)

print_title(
    "fill in all health script informations. Fields suffixed with [red](*)[/] are mandatory"
)

while not (pkg_name := Prompt.ask("[cyan]name [red](*)")):
    pass
pkg_name = pkg_name.casefold().replace(" ", "_")

while not (pkg_description := Prompt.ask("[cyan]description [red](*)")):
    pass


all_packages = Custom().get_packages()
package_managers = get_package_managers()

print_title("Dependencies")
print(
    'dependencies are structured like "packagemanager:name". Ex:  apt:ping, custom:package'
)
print(
    "available package managers: "
    + ", ".join(f"[cyan]{pm.name}[/]" for pm in package_managers)
)
print(
    "available custom dependencies: "
    + ", ".join(f"[cyan]{pkg.name}[/]" for pkg in all_packages)
)
print("\nleave empty for no dependencies")

pkg_dependencies = list(filter(str, [Prompt.ask("[cyan]dependency name")]))
while pkg_dependencies and Confirm.ask(
    "[cyan]there are any additional dependencies?", default=False  # type: ignore
):
    pkg_dependencies = list(
        filter(
            str,
            [*pkg_dependencies, Prompt.ask("[cyan]dependency name")],
        )
    )

pkg_url = ""
pkg_sources = []

new_pkg = Package(
    pkg_name,
    pkg_description,
    pkg_url,
    pkg_dependencies,
    pkg_sources,
    str(effective_health_folder / pkg_name / "PKGBUILD"),
    ["check", "install", "uninstall"],
)

are_custom_packages_valid([*all_packages, new_pkg])

new_pkgbuild = generate_pkgbuild_template(
    pkg_name=pkg_name,
    pkg_description=pkg_description,
    pkg_dependencies=pkg_dependencies,
    platform=PLATFORM,
    is_health_script=True,
)

os.makedirs(effective_health_folder / pkg_name, exist_ok=True)
with open(effective_health_folder / pkg_name / "PKGBUILD", "w") as f:
    f.write(new_pkgbuild + "\n")

if Confirm.ask("Open PKGBUILD on default EDITOR?", default=True):  # type: ignore
    default_editor(effective_health_folder / pkg_name / "PKGBUILD")


