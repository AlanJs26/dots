"""
ARCHDOTS
help: sync packages
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

import sys
from rich import print
from src.package_manager import PackageManager, package_managers
from src.settings import read_config

config = read_config()

if "pkgs" not in config:
    print("there is no pkgs configured", file=sys.stderr)
    exit()

packages_by_pm = {pm: pm.get_installed() for pm in package_managers}

pending_packages: dict[PackageManager, list[str]] = {}
for pm in packages_by_pm:
    if pm not in config["pkgs"]:
        continue
    pending_packages[pm] = list(set(config["pkgs"][pm]) - set(packages_by_pm[pm]))

for pm, packages in pending_packages.items():
    pm.install(packages)


# unmanaged_packages: dict[str, list[str]] = {}
# for pm in config["pkgs"]:
#     if pm not in packages_by_pm:
#         continue
#     unmanaged_packages[pm] = list(set(packages_by_pm[pm]) - set(config["pkgs"][pm]))

# :TODO: Finish this script. Need to install pending packages (custom and external) and run review command on unmanaged packages
