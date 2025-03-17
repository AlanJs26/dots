"""
ARCHDOTS
help: check the status of all health scripts
arguments:
  - name: name
    required: false
    type: str
    nargs: "*"
    help: script to check. Leave empty for all
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

from rich import print

from archdots.constants import HEALTH_FOLDER
from archdots.package import get_packages
import os

os.makedirs(HEALTH_FOLDER, exist_ok=True)
packages = get_packages(HEALTH_FOLDER)

packages_by_name = {pkg.name: pkg for pkg in packages}

if args["name"]:
    for name in args["name"]:
        if name not in packages_by_name:
            print(f'unknown health script "{name}"')
            exit()
    packages = [packages_by_name[pkg_name] for pkg_name in args["name"]]

for pkg in packages:
    status = pkg.check(supress_output=True)
    status_color = "[green]" if status else "[red]"
    status_suffix = "" if status else " (unconfigured)"
    print(f"{status_color}{pkg.name} : {pkg.description}{status_suffix}")
