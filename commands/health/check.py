"""
ARCHDOTS
help: check the status of all health scripts
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

for pkg in packages:
    status = pkg.check(supress_output=True)
    status_color = "[green]" if status else "[red]"
    status_suffix = "" if status else " (unconfigured)"
    print(f"{status_color}{pkg.name} : {pkg.description}{status_suffix}")
