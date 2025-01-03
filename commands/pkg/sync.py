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
from archdots.package_manager import PackageManager, package_managers, Custom
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
flatten_pending_packages: list[str] = []
for pm in packages_by_pm:
    if pm not in config["pkgs"]:
        continue
    pending_packages[pm] = list(set(config["pkgs"][pm]) - set(packages_by_pm[pm]))
    flatten_pending_packages.extend(f"{pm}:{pkg}" for pkg in pending_packages[pm])


if any(pkgs for pkgs in pending_packages.values()):
    print(
        f'[cyan]::[/] about to install the following pending packages: [cyan]{"  ".join(flatten_pending_packages)}'
    )
    if Confirm.ask("[cyan]::[/] Proceed?", default=True):
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
    "[cyan]:: [/]there are unmanaged packages. Review?", default=True  # type: ignore
):
    path = Path(MODULE_PATH) / "commands/pkg/review.py"
    spec = importlib.util.spec_from_file_location(os.path.basename(path), path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        module.__dict__["args"] = {}
        spec.loader.exec_module(module)
else:
    from rich.console import Console

    warning_console = Console(style="yellow italic", stderr=True)

    lost_packages = set(pkg.name for pkg in Custom().get_packages(True)).difference(
        Custom().get_installed(True)
    )
    if "custom" in config["pkgs"]:
        lost_packages = lost_packages.difference(config["pkgs"]["custom"])

    if lost_packages:
        warning_console.print(
            "\nFound packages that have been configured but aren't installed neither listed in config.yaml",
            "To remove this warning, delete those packages or add them to config.yaml\n",
            f'packages: {", ".join(lost_packages)}',
            sep="\n",
        )

if not any(pkgs for pkgs in pending_packages.values()) and not unmanaged_packages:
    print("[green]Already Synced")
