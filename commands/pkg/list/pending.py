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
from archdots.ui.console import print_title
from archdots.packages.filters import get_pending_packages

pending_packages = {
    pm.name: pkgs
    for pm, pkgs in get_pending_packages(use_memo=True).items()
}

if not any(pkgs for pkgs in pending_packages.values()):
    print("there are no pending packages", file=sys.stderr)
    exit()

for name, pkgs in pending_packages.items():
    if not pkgs:
        continue
    if args["filter"] and name not in args["filter"]:
        continue
    print_title(f"{name}")
    for pkg_name in pkgs:
        print(pkg_name)


