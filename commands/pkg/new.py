"""
ARCHDOTS
help: create a new custom package
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
from archdots.core.constants import PACKAGES_FOLDER, PLATFORM
from archdots.core.platforms.registry import get_all_platforms
from pathlib import Path

import os

valid_platforms = [p.name for p in get_all_platforms()]
if any(
    Path(PACKAGES_FOLDER).joinpath(d).is_dir()
    for d in valid_platforms
    if Path(PACKAGES_FOLDER).exists()
):
    effective_packages_folder = Path(PACKAGES_FOLDER) / PLATFORM
else:
    effective_packages_folder = Path(PACKAGES_FOLDER)

os.makedirs(effective_packages_folder, exist_ok=True)

print_title(
    "fill in all package informations. Fields suffixed with [red](*)[/] are mandatory"
)

while not (pkg_name := Prompt.ask("[cyan]package name [red](*)")):
    pass
pkg_name = pkg_name.casefold().replace(" ", "_")
while not (pkg_description := Prompt.ask("[cyan]package description [red](*)")):
    pass
while not (pkg_url := Prompt.ask("[cyan]package url (where to find it) [red](*)")):
    pass

pkg_sources = list(
    filter(str, [Prompt.ask("[cyan]package source (downloadable resource)")])
)

while pkg_sources and Confirm.ask(
    "[cyan]there are any additional sources?", default=False  # type: ignore
):
    pkg_sources = list(
        filter(
            str,
            [
                *pkg_sources,
                Prompt.ask("[cyan]package source (downloadable resource)"),
            ],
        )
    )

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

new_pkg = Package(
    pkg_name,
    pkg_description,
    pkg_url,
    pkg_dependencies,
    pkg_sources,
    str(effective_packages_folder / pkg_name / "PKGBUILD"),
    ["check", "install", "uninstall"],
)

are_custom_packages_valid([*all_packages, new_pkg])

new_pkgbuild = generate_pkgbuild_template(
    pkg_name=pkg_name,
    pkg_description=pkg_description,
    pkg_dependencies=pkg_dependencies,
    platform=PLATFORM,
    pkg_url=pkg_url,
    pkg_sources=pkg_sources,
    is_health_script=False,
)

os.makedirs(effective_packages_folder / pkg_name, exist_ok=True)
with open(effective_packages_folder / pkg_name / "PKGBUILD", "w") as f:
    f.write(new_pkgbuild + "\n")

if Confirm.ask(f"Add {pkg_name} as a managed package?", default=True):  # type: ignore
    from archdots.config.manager import ConfigManager

    config = ConfigManager().load()
    if "pkgs" not in config:
        config["pkgs"] = {}
    if "custom" not in config["pkgs"]:
        config["pkgs"]["custom"] = []
    config["pkgs"]["custom"].append(pkg_name)
    ConfigManager().save(config)

if Confirm.ask("Open PKGBUILD on default EDITOR?", default=True):  # type: ignore
    default_editor(effective_packages_folder / pkg_name / "PKGBUILD")


