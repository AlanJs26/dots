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
from archdots.console import print_title
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
    import inquirer

    questions = [
        inquirer.List(
            "result",
            message="Choose which package to edit",
            choices=[pkg.name for pkg in all_packages],
        ),
    ]
    answer = inquirer.prompt(questions) or exit()

    selected_package = (
        next(filter(lambda pkg: pkg.name == answer["result"], all_packages), None)
        or exit()
    )


default_editor(selected_package.pkgbuild)
