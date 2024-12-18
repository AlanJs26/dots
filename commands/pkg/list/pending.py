"""
ARCHDOTS
help: list pending packages
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

import sys
from src.package import get_packages
from pathlib import Path
from rich import print
from src.package_manager import package_managers
from src.settings import read_config
from src.constants import MODULE_PATH


packages = {pm.name: pm.get_installed() for pm in package_managers}

custom_packages = get_packages(str(Path(MODULE_PATH) / "packages"))

packages["custom"] = [
    pkg.name for pkg in custom_packages if pkg.check(supress_output=True)
]

config = read_config()

if "pkgs" not in config:
    print("there is no pkgs configured", file=sys.stderr)
    exit()

pending_packages: dict[str, list[str]] = {}
for k in packages:
    if k not in config["pkgs"]:
        continue
    pending_packages[k] = list(set(config["pkgs"][k]) - set(packages[k]))

for name, pkgs in pending_packages.items():
    if not pkgs:
        continue
    print(f"[cyan]:: [/]{name}")
    for pkg_name in pkgs:
        print(pkg_name)
