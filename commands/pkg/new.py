"""
ARCHDOTS
help: create a new custom package
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

from archdots.console import print_title
from archdots.package import Package
from archdots.package_manager import package_managers, are_custom_packages_valid, Custom
from archdots.utils import default_editor
from rich import print
from rich.prompt import Prompt, Confirm
from archdots.constants import PACKAGES_FOLDER, PLATFORM
from pathlib import Path

import os

os.makedirs(PACKAGES_FOLDER, exist_ok=True)

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
    str(Path(PACKAGES_FOLDER) / pkg_name / "PKGBUILD"),
    ["check", "install", "uninstall"],
)

are_custom_packages_valid([*all_packages, new_pkg])

new_pkgbuild = f'''
description='{pkg_description.replace("'", "\\'")}'
url='{pkg_url.replace("'", "\\'")}'
depends=({' '.join(f"'{dep}'" for dep in pkg_dependencies)})
source=({' '.join(f"'{source}'" for source in pkg_sources)})
# make this package platform specific. Supported platforms: linux, windows 
platform='{PLATFORM}'

# All items of source will be downloaded and extracted (when necessary)
# all downloaded (or extracted folders) are stored inside ${{sourced[@]}}
# This script runs inside a folder over ~/.cache/archdots/pkgname, where all sources are downloaded
#
# $PKGPATH has the path to folder containing this file 

# This function install the package on the system
install() {{
    echo "message from install() of {pkg_name}" 
}}

# This function uninstall the package from the system
uninstall() {{
    echo "message from uninstall() of {pkg_name}" 
}}

# This function should end with exit code 0 when the package is installed on system
# and end with exit code 1 when it is uninstalled
check() {{
    echo "message from check() of {pkg_name}" 
}}
'''

os.makedirs(Path(PACKAGES_FOLDER) / pkg_name, exist_ok=True)
with open(Path(PACKAGES_FOLDER) / pkg_name / "PKGBUILD", "w") as f:
    f.write(new_pkgbuild.strip())

if Confirm.ask(f"Add {pkg_name} as a managed package?", default=True):  # type: ignore
    from archdots.settings import read_config, save_config

    config = read_config()
    if "pkgs" not in config:
        config["pkgs"] = {}
    if "custom" not in config["pkgs"]:
        config["pkgs"]["custom"] = []
    config["pkgs"]["custom"].append(pkg_name)
    save_config(config)

if Confirm.ask("Open PKGBUILD on default EDITOR?", default=True):  # type: ignore
    default_editor(Path(PACKAGES_FOLDER) / pkg_name / "PKGBUILD")
