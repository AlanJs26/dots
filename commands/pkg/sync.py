"""
ARCHDOTS
help: sync packages
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

import sys
from rich import print
from archdots.constants import MODULE_PATH
from archdots.package_manager import PackageManager, package_managers
from archdots.settings import read_config
from rich.prompt import Confirm
import importlib.util
from pathlib import Path
import os

config = read_config()

if "pkgs" not in config:
    print("there is no pkgs configured", file=sys.stderr)
    exit()

packages_by_pm = {pm.name: pm.get_installed() for pm in package_managers}
pm_by_name: dict[str, PackageManager] = {pm.name: pm for pm in package_managers}

pending_packages: dict[str, list[str]] = {}
for pm in packages_by_pm:
    if pm not in config["pkgs"]:
        continue
    pending_packages[pm] = list(set(config["pkgs"][pm]) - set(packages_by_pm[pm]))

for pm_name, packages in pending_packages.items():
    pm_by_name[pm_name].install(packages)

unmanaged_packages: list[str] = []
for pm in config["pkgs"]:
    if pm not in packages_by_pm:
        continue
    unmanaged_packages.extend(set(packages_by_pm[pm]) - set(config["pkgs"][pm]))

if unmanaged_packages and Confirm.ask(
    "[cyan]:: [/]there are unmanaged packages. Review?", default=True  # type: ignore
):
    path = Path(MODULE_PATH) / "commands/pkg/review.py"
    spec = importlib.util.spec_from_file_location(os.path.basename(path), path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
