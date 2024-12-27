"""
ARCHDOTS
help: list pending packages
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
from src.package_manager import package_managers
from src.settings import read_config

installed_pkgs_by_pm = {pm.name: pm.get_installed() for pm in package_managers}

config = read_config()

if "pkgs" not in config:
    print("there is no pkgs configured", file=sys.stderr)
    exit()

pending_packages: dict[str, list[str]] = {}
for pm_name in installed_pkgs_by_pm:
    if pm_name not in config["pkgs"]:
        continue
    pending_packages[pm_name] = list(
        set(config["pkgs"][pm_name]) - set(installed_pkgs_by_pm[pm_name])
    )

for name, pkgs in pending_packages.items():
    if not pkgs:
        continue
    if args["filter"] and name not in args["filter"]:
        continue
    print(f"[cyan]:: [/]{name}")
    for pkg_name in pkgs:
        print(pkg_name)
