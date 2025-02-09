"""
ARCHDOTS
help: open a health script in default editor
arguments:
  - name: name
    required: false
    type: str
    help: script to edit
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

from archdots.console import print_title
from archdots.utils import default_editor
from rich import print
from archdots.constants import HEALTH_FOLDER
from archdots.package import get_packages

all_packages = get_packages(HEALTH_FOLDER)
packages_by_name = {pkg.name: pkg for pkg in all_packages}

if name := args["name"]:
    if name not in packages_by_name:
        print(f'unknown health script "{name}"')
        exit()
    selected_package = packages_by_name[name]
else:
    import inquirer

    questions = [
        inquirer.List(
            "result",
            message="Choose which heath script to edit",
            choices=[pkg.name for pkg in all_packages],
        ),
    ]
    answer = inquirer.prompt(questions) or exit()

    selected_package = (
        next(filter(lambda pkg: pkg.name == answer["result"], all_packages), None)
        or exit()
    )

default_editor(selected_package.pkgbuild)
