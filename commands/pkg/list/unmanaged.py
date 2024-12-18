"""
ARCHDOTS
help: list unmanaged packages
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

packages = {pm.name: pm.get_installed() for pm in package_managers}

config = read_config()

if "pkgs" not in config:
    print("there is no pkgs configured", file=sys.stderr)
    exit()

unmanaged_packages: dict[str, list[str]] = {}
for k in config["pkgs"]:
    if k not in packages:
        continue
    unmanaged_packages[k] = list(set(packages[k]) - set(config["pkgs"][k]))

for name, pkgs in unmanaged_packages.items():
    if not pkgs:
        continue
    if args["filter"] and name not in args["filter"]:
        continue
    print(f"[cyan]:: [/]{name}")
    for pkg_name in pkgs:
        print(pkg_name)
