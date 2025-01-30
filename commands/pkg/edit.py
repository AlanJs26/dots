"""
ARCHDOTS
help: open a custom package in default editor
arguments:
  - name: name
    required: false
    type: str
    help: package to edit
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

from rich import print
from archdots.utils import default_editor
from archdots.package_manager import Custom

all_packages = Custom().get_packages()
packages_by_name = {pkg.name: pkg for pkg in all_packages}

name = args["name"]
if name:
    if name not in packages_by_name:
        print(f'unknown package "{name}"')
        exit()
    selected_package = packages_by_name[name]
else:
    from simple_term_menu import TerminalMenu
    print("[cyan]:: [/]Choose which package to edit")

    terminal_menu = TerminalMenu(
        [pkg.name for pkg in all_packages], show_search_hint=True
    )
    menu_entry_index = terminal_menu.show()

    if not isinstance(menu_entry_index, int):
        exit()

    selected_package = all_packages[menu_entry_index]

default_editor(selected_package.pkgbuild)
