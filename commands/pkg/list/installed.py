"""
ARCHDOTS
help: list installed packages
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

from rich import print
from src.package_manager import package_managers

packages = {pm.name: pm.get_installed() for pm in package_managers}

for name, pkgs in packages.items():
    print(f"[cyan]:: [/]{name}")
    for pkg_name in pkgs:
        print(pkg_name)
