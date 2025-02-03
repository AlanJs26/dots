"""
ARCHDOTS
help: packages in config.yaml that aren't installed
flags:
    - long: --filter
      type: str
      nargs: +
      help: filter by one or more package managers
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

import sys
from rich import print
from archdots.console import print_title
from archdots.package_manager import package_managers, Custom
from archdots.settings import read_config

installed_pkgs_by_pm = {pm.name: pm.get_installed() for pm in package_managers}

custom_pkg_names = [pkg.name for pkg in Custom().get_packages(use_memo=True)]

config = read_config()

if "pkgs" not in config:
    print("there is no pkgs configured", file=sys.stderr)
    exit()

pending_packages: dict[str, list[str]] = {}
all_obscured_packages: list[str] = []
for pm_name in installed_pkgs_by_pm:
    if pm_name not in config["pkgs"]:
        continue
    obscured_packages = set()
    if pm_name != Custom().name:
        obscured_packages = set(custom_pkg_names).intersection(config["pkgs"][pm_name])
        all_obscured_packages.extend(f"{pm_name}:{pkg}" for pkg in obscured_packages)

    pending_packages[pm_name] = list(
        set(config["pkgs"][pm_name])
        - set(installed_pkgs_by_pm[pm_name])
        - obscured_packages
    )

for name, pkgs in pending_packages.items():
    if not pkgs:
        continue
    if args["filter"] and name not in args["filter"]:
        continue
    print_title(f"{name}")
    for pkg_name in pkgs:
        print(pkg_name)
