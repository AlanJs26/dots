"""
ARCHDOTS
help: delete a custom package
arguments:
  - name: name
    required: false
    type: str
    nargs: "*"
    help: package to delete
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

from archdots.exceptions import PackageException
from archdots.package_manager import Custom
from rich import print
from rich.prompt import Confirm
from archdots.constants import CONFIG_FOLDER
from pathlib import Path

import shutil

from archdots.settings import read_config, save_config

PACKAGES_PATH = Path(CONFIG_FOLDER) / "packages"

all_packages = Custom().get_packages()
packages_by_name = {pkg.name: pkg for pkg in all_packages}

if not all_packages:
    print("there are any packages delete")
    exit()

if args["name"]:
    for name in args["name"]:
        if name not in packages_by_name:
            print(f'unknown health script "{name}"')
            exit()
    selected_packages = [packages_by_name[pkg_name] for pkg_name in args["name"]]
else:
    from simple_term_menu import TerminalMenu

    print("[cyan]:: [/]Choose packages to delete")

    terminal_menu = TerminalMenu(
        [pkg.name for pkg in all_packages],
        multi_select=True,
        multi_select_select_on_accept=False,
        multi_select_empty_ok=True,
        show_multi_select_hint=True,
    )
    terminal_menu.show()

    if not terminal_menu.chosen_menu_entries:
        exit()

    selected_packages = [
        packages_by_name[pkg_name] for pkg_name in terminal_menu.chosen_menu_entries
    ]

if not Confirm.ask(
    f'[cyan]:: [/]are you sure you want to delete {",".join(terminal_menu.chosen_menu_entries)}?', default=False  # type: ignore
):
    exit()

settings = read_config()

for pkg in selected_packages:
    if pkg.check(supress_output=True):
        print(f'[red]uninstalling "{pkg.name}"')
        if not pkg.uninstall():
            raise PackageException(f"Could not uninstall {pkg.name}")
    print(f'[red]removing "{Path(pkg.pkgbuild).parent}"')
    shutil.rmtree(Path(pkg.pkgbuild).parent)
    if (
        "pkg" in settings
        and "custom" in settings["pkg"]
        and pkg.name in settings["pkg"]["custom"]
    ):
        settings["pkg"]["custom"].remove(pkg.name)

save_config(settings)
