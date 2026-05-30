"""
ARCHDOTS
help: list all health scripts
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

from rich import print

from archdots.core.constants import HEALTH_FOLDER
from archdots.packages.package import get_packages


packages = get_packages(HEALTH_FOLDER)

if not packages:
    print("there are any health scripts to list")
    exit()

for pkg in packages:
    print(f"[cyan]{pkg.name}[/] : {pkg.description}")
