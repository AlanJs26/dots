"""
ARCHDOTS
help: create a new health script
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
from archdots.constants import HEALTH_FOLDER, PLATFORM
from pathlib import Path

import os

os.makedirs(HEALTH_FOLDER, exist_ok=True)

print_title(
    "fill in all health script informations. Fields suffixed with [red](*)[/] are mandatory"
)

while not (pkg_name := Prompt.ask("[cyan]name [red](*)")):
    pass
pkg_name = pkg_name.casefold().replace(" ", "_")

while not (pkg_description := Prompt.ask("[cyan]description [red](*)")):
    pass


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

pkg_url = ""
pkg_sources = []

new_pkg = Package(
    pkg_name,
    pkg_description,
    pkg_url,
    pkg_dependencies,
    pkg_sources,
    str(Path(HEALTH_FOLDER) / pkg_name / "PKGBUILD"),
    ["check", "install", "uninstall"],
)

are_custom_packages_valid([*all_packages, new_pkg])

new_pkgbuild = f'''
description='{pkg_description.replace("'", "'\"'\"'")}'
url=''
depends=({' '.join(f"'{dep}'" for dep in pkg_dependencies)})
source=()
# make this health script platform specific. Supported platforms: linux, windows 
platform='{PLATFORM}'

# All items of source will be downloaded and extracted (when necessary)
# all downloaded (or extracted folders) are stored inside ${{sourced[@]}}
# This script is ran inside a folder over ~/.cache/archdots/pkgname, where all sources are downloaded
#
# $PKGPATH has the path to folder containing this file 

# This function is used to configure the health script
install() {{
    echo "message from install() of {pkg_name}" 
}}

# This function is used to unconfigure the health script
uninstall() {{
    echo "message from uninstall() of {pkg_name}" 
}}

# This function should end with exit code 0 when the health script is configured
# and end with exit code 1 when it is unconfigured
check() {{
    echo "message from check() of {pkg_name}" 
}}
'''

os.makedirs(Path(HEALTH_FOLDER) / pkg_name, exist_ok=True)
with open(Path(HEALTH_FOLDER) / pkg_name / "PKGBUILD", "w") as f:
    f.write(new_pkgbuild.strip())

if Confirm.ask("Open PKGBUILD on default EDITOR?", default=True):  # type: ignore
    default_editor(Path(HEALTH_FOLDER) / pkg_name / "PKGBUILD")
