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

from rich import print

from archdots.console import print_title
from archdots.package import get_packages
from archdots.constants import HEALTH_FOLDER


all_packages = [
    pkg for pkg in get_packages(HEALTH_FOLDER) if pkg.check(supress_output=True)
]

packages_by_name = {pkg.name: pkg for pkg in all_packages}

if not all_packages:
    print("there are any health scripts to unconfigure")
    exit()

if args["name"]:
    for name in args["name"]:
        if name not in packages_by_name:
            print(f'unknown health script "{name}"')
            exit()
    selected_packages = [packages_by_name[pkg_name] for pkg_name in args["name"]]
else:
    import inquirer

    questions = [
        inquirer.Checkbox(
            "result",
            message="Choose health scripts to unconfigure",
            choices=[pkg.name for pkg in all_packages],
        ),
    ]
    answers = inquirer.prompt(questions) or exit()

    selected_packages = [packages_by_name[pkg_name] for pkg_name in answers["result"]]

for pkg in selected_packages:
    print_title(f'Unconfiguring "{pkg.name}"')
    if not pkg.uninstall():
        print_title(f'Failed to unconfigure "{pkg.name}', color="red")
