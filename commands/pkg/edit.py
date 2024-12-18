from src.package import get_packages
from simple_term_menu import TerminalMenu
from rich import print
from src.constants import CONFIG_FOLDER
from pathlib import Path

import os

PACKAGES_PATH = Path(CONFIG_FOLDER) / "packages"
print("[cyan]:: [/]Choose which package to edit")

all_packages = get_packages(str(PACKAGES_PATH))
packages_by_name = {pkg.name: pkg for pkg in all_packages}

terminal_menu = TerminalMenu([pkg.name for pkg in all_packages], show_search_hint=True)
menu_entry_index = terminal_menu.show()

if not isinstance(menu_entry_index, int):
    exit()

selected_package = all_packages[menu_entry_index]

os.system(f'$EDITOR "{selected_package.pkgbuild}"')

