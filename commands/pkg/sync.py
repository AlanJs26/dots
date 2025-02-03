"""
ARCHDOTS
help: sync packages
flags:
    - long: --install
      type: str
      nargs: +
      help: try to install package, independently of managed state
    - long: --uninstall
      type: str
      nargs: +
      help: try to uninstall package, independently of managed state
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

import sys
from rich import print
from archdots.constants import MODULE_PATH
from archdots.package_manager import (
    PackageManager,
    package_managers,
    Custom,
    split_packages_by_pm,
)
from archdots.settings import read_config
from archdots.console import title, warn_console, print_title
from rich.prompt import Confirm
import importlib.util
from pathlib import Path
import os

if args["install"]:
    pkgs_by_pm = split_packages_by_pm(args["install"])
    for pm, pkgs in pkgs_by_pm.items():
        pm.install(pkgs)
if args["uninstall"]:
    pkgs_by_pm = split_packages_by_pm(args["uninstall"])
    for pm, pkgs in pkgs_by_pm.items():
        pm.uninstall(pkgs)

if args["install"] or args["uninstall"]:
    exit()

config = read_config()

if "pkgs" not in config:
    print("there is no pkgs configured", file=sys.stderr)
    exit()

packages_by_pm: dict[str, list[str]] = {
    pm.name: pm.get_installed() for pm in package_managers
}
pm_by_name: dict[str, PackageManager] = {pm.name: pm for pm in package_managers}

custom_pkg_names = [pkg.name for pkg in Custom().get_packages(use_memo=True)]

pending_packages: dict[str, list[str]] = {}
flatten_pending_packages: list[str] = []
all_obscured_packages: list[str] = []
for pm in packages_by_pm:
    if pm not in config["pkgs"]:
        continue
    obscured_packages = set()
    if pm != Custom().name:
        obscured_packages = set(custom_pkg_names).intersection(config["pkgs"][pm])
        all_obscured_packages.extend(f"{pm}:{pkg}" for pkg in obscured_packages)

    pending_packages[pm] = list(
        set(config["pkgs"][pm]) - set(packages_by_pm[pm]) - obscured_packages
    )
    flatten_pending_packages.extend(f"{pm}:{pkg}" for pkg in pending_packages[pm])

if all_obscured_packages:
    warn_console.print(
        f'the packages {", ".join(all_obscured_packages)} were obscured by custom packages with same name. Consider removing them from your config'
    )

if any(pkgs for pkgs in pending_packages.values()):
    print_title(
        f'about to install the following pending packages: [cyan]{"  ".join(flatten_pending_packages)}'
    )
    if Confirm.ask(title("Proceed?"), default=True):
        for pm_name, packages in pending_packages.items():
            if not packages:
                continue
            print()
            pm_by_name[pm_name].install(packages)

unmanaged_packages: list[str] = []
for pm in config["pkgs"]:
    if pm not in packages_by_pm:
        continue
    unmanaged_packages.extend(set(packages_by_pm[pm]) - set(config["pkgs"][pm]))

if unmanaged_packages and Confirm.ask(
    title("there are unmanaged packages. Review?"), default=True  # type: ignore
):
    path = Path(MODULE_PATH) / "commands/pkg/review.py"
    spec = importlib.util.spec_from_file_location(os.path.basename(path), path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        module.__dict__["args"] = {}
        spec.loader.exec_module(module)
else:

    lost_packages = set(pkg.name for pkg in Custom().get_packages(True)).difference(
        Custom().get_installed(True)
    )
    if "custom" in config["pkgs"]:
        lost_packages = lost_packages.difference(config["pkgs"]["custom"])

    if lost_packages:
        warn_console.print(
            "\nFound packages that have been configured but aren't installed neither listed in config.yaml",
            "To remove this warning, delete those packages or add them to config.yaml\n",
            f'packages: {", ".join(lost_packages)}',
            sep="\n",
        )

if not any(pkgs for pkgs in pending_packages.values()) and not unmanaged_packages:
    print("[green]Already Synced")
