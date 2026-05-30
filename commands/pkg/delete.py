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

from archdots.ui.console import print_title, title
from archdots.core.exceptions import PackageException
from archdots.packages.managers import Custom
from rich import print
from rich.prompt import Confirm
from archdots.core.constants import CONFIG_FOLDER
from pathlib import Path

import shutil

from archdots.config.manager import ConfigManager

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
    import inquirer

    questions = [
        inquirer.Checkbox(
            "result",
            message="Choose packages to delete",
            choices=[pkg.name for pkg in all_packages],
        ),
    ]
    answers = inquirer.prompt(questions) or exit()

    selected_packages = [packages_by_name[pkg_name] for pkg_name in answers["result"]]

if not selected_packages or not Confirm.ask(
    title(f'are you sure you want to delete {",".join(pkg.name for pkg in selected_packages)}?'), default=False  # type: ignore
):
    exit()

settings = ConfigManager().load()

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

ConfigManager().save(settings)


