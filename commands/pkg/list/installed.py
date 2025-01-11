"""
ARCHDOTS
help: installed (and managed) packages
flags:
    - long: --filter
      type: str
      nargs: +
      help: filter by one or more package managers
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

from rich import print
from archdots.package_manager import package_managers
from archdots.settings import read_config

config = read_config()

if "pkgs" not in config:
    import sys
    print("there is no pkgs configured", file=sys.stderr)
    exit()

packages = {pm.name: pm.get_installed() for pm in package_managers}

for name, pkgs in packages.items():
    if not pkgs:
        continue
    if args["filter"] and name not in args["filter"]:
        continue
    if name not in config['pkgs']:
        continue

    print(f"[cyan]:: [/]{name}")
    for pkg_name in pkgs:
        if pkg_name not in config['pkgs'][name]:
            continue
        print(pkg_name)
