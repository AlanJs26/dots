"""
ARCHDOTS
help: list installed packages
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

from src.package import get_packages
from pathlib import Path
from rich import print
from src.package_manager import package_managers

from src.constants import MODULE_PATH

packages = {pm.name: pm.get_installed() for pm in package_managers}

custom_packages = get_packages(str(Path(MODULE_PATH) / "packages"))

packages["custom"] = [pkg.name for pkg in custom_packages if pkg.check()]


for name, pkgs in packages.items():
    print(f"[cyan]:: [/]{name}")
    for pkg_name in pkgs:
        print(pkg_name)

# print(custom_packages)
# print(packages)
