from src.package import PackageException, get_packages
from simple_term_menu import TerminalMenu
from rich import print
from rich.prompt import Confirm
from src.constants import CONFIG_FOLDER
from pathlib import Path

import shutil

from src.settings import read_config, save_config

PACKAGES_PATH = Path(CONFIG_FOLDER) / "packages"
print("[cyan]:: [/]Choose packages to delete")

all_packages = get_packages(str(PACKAGES_PATH))
packages_by_name = {pkg.name: pkg for pkg in all_packages}

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
    if pkg.check():
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
