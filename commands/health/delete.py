"""
ARCHDOTS
help: delete a health script
arguments:
  - name: name
    required: false
    type: str
    nargs: "*"
    help: script to delete
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

from archdots.console import print_title, title
from archdots.package import get_packages
from archdots.exceptions import PackageException
from rich import print
from rich.prompt import Confirm
from archdots.constants import HEALTH_FOLDER
from pathlib import Path

import shutil

all_packages = get_packages(HEALTH_FOLDER)
packages_by_name = {pkg.name: pkg for pkg in all_packages}

if not all_packages:
    print("there are any health scripts to delete")
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
            message="Choose health scripts to delete",
            choices=[pkg.name for pkg in all_packages],
        ),
    ]
    answers = inquirer.prompt(questions)

    if not answers:
        exit()

    selected_packages = [packages_by_name[pkg_name] for pkg_name in answers["result"]]


if not selected_packages or not Confirm.ask(
    title(f'are you sure you want to delete {",".join(pkg.name for pkg in selected_packages)}?'), default=False  # type: ignore
):
    exit()

for pkg in selected_packages:
    if pkg.check(supress_output=True):
        print(f'[red]unconfiguring "{pkg.name}"')
        if not pkg.uninstall():
            raise PackageException(f"Could not unconfigure {pkg.name}")
    print(f'[red]removing "{Path(pkg.pkgbuild).parent}"')
    shutil.rmtree(Path(pkg.pkgbuild).parent)
