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

packages = {pm.name: pm.get_installed() for pm in package_managers}

for name, pkgs in packages.items():
    if not pkgs:
        continue
    if args["filter"] and name not in args["filter"]:
        continue

    print(f"[cyan]:: [/]{name}")
    for pkg_name in pkgs:
        print(pkg_name)
