"""
ARCHDOTS
help: unconfigure health scripts
arguments:
  - name: name
    required: false
    type: str
    nargs: "*"
    help: script to unconfigure
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

from simple_term_menu import TerminalMenu
from rich import print

from archdots.package import get_packages
from archdots.constants import HEALTH_FOLDER


all_packages = [
    pkg for pkg in get_packages(HEALTH_FOLDER) if pkg.check(supress_output=True)
]

packages_by_name = {pkg.name: pkg for pkg in all_packages}

if not all_packages:
    print("there are any health scripts configured")
    exit()

if args["name"]:
    for name in args["name"]:
        if name not in packages_by_name:
            print(f'unknown health script "{name}"')
            exit()
    selected_packages = [packages_by_name[pkg_name] for pkg_name in args["name"]]
else:
    print("[cyan]:: [/]Choose health scripts to unconfigure")

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

for pkg in selected_packages:
    print(f'[cyan]:: [/]Unconfiguring "{pkg.name}"')
    if not pkg.uninstall():
        print(f'[red]:: [/] Failed to unconfigure "{pkg.name}')
