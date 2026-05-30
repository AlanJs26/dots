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
from archdots.ui.console import print_title
from archdots.packages.filters import get_managed_packages

packages = {
    pm.name: pkgs
    for pm, pkgs in get_managed_packages(use_memo=True).items()
}

for name, pkgs in packages.items():
    if not pkgs:
        continue
    if args["filter"] and name not in args["filter"]:
        continue

    print_title(f"{name}")
    for pkg_name in pkgs:
        print(pkg_name)


