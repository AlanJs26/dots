"""
ARCHDOTS
help: setup chezmoi and default packages
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

import os
from pathlib import Path
import shutil
from rich import print
from archdots.console import print_title, prompt, transient_progress
from archdots.constants import CHEZMOI_FOLDER, CONFIG_FOLDER, MODULE_PATH
from archdots.exceptions import CommandException
from archdots.package import get_packages
from archdots.console import warn_console, confirm
from archdots.package_manager import split_external_dependencies
from archdots.utils import is_url_valid
from shutil import which

with transient_progress("checking packages"):
    default_pkgs = [
        pkg
        for pkg in get_packages(Path(MODULE_PATH) / "default_packages")
        if not pkg.check(supress_output=True)
    ]
    ext_dependencies_by_pm, sorted_packages = split_external_dependencies(
        default_pkgs, default_pkgs
    )
    default_pkgs = sorted_packages

if default_pkgs:
    warn_console.print(
        'This message can be ignored by setting "default_packages: false" on config.yaml'
    )
    print_title("There are unsatisfied dependencies")

    if confirm(
        f'Ready to install: {", ".join(pkg.name for pkg in default_pkgs)}?',
        default=True,
    ):
        for pkg in default_pkgs:
            pkg.install()

if os.path.isdir(Path(CHEZMOI_FOLDER) / ".git"):
    print_title(f'chezmoi folder already exists at "{CHEZMOI_FOLDER}"', color="yellow")

CHEZMOI_AVAILABLE = which("chezmoi") is not None

if CHEZMOI_AVAILABLE:
    if confirm("initialize chezmoi from scratch?", default=True):
        GIT_INITIALIZED = os.path.isdir(Path(CHEZMOI_FOLDER) / '.git')
        if not GIT_INITIALIZED or confirm('a git repository was already initialized. Run chezmoi init anyway?', default=False):
            os.system("chezmoi init && chezmoi git -- branch -M main")

        os.makedirs(CHEZMOI_FOLDER, exist_ok=True)

        if os.path.isdir(CONFIG_FOLDER):
            shutil.copytree(
                CONFIG_FOLDER,
                Path(CHEZMOI_FOLDER) / Path(CONFIG_FOLDER).stem,
                dirs_exist_ok=True,
            )
        else:
            os.makedirs(Path(CHEZMOI_FOLDER) / Path(CONFIG_FOLDER).stem, exist_ok=True)

        if not GIT_INITIALIZED:
            print_title("initializing git repository")

        prev_cwd = os.getcwd()
        os.chdir(CHEZMOI_FOLDER)

        if confirm("use default template?", default=True):
            template_path = Path(MODULE_PATH) / "chezmoi_template"
            shutil.copytree(template_path, CHEZMOI_FOLDER, dirs_exist_ok=True)

        os.system('git add . && git commit -m ":tada: Init chezmoi"')

        warn_console.print("leave empty to ignore")
        git_origin = prompt("remote git origin")

        if git_origin:
            os.system(f"git remote add origin {git_origin}")

            os.system("git push -u origin main")

        os.system("chezmoi apply -v")

        os.chdir(prev_cwd)
    else:
        git_origin = prompt("remote git origin")
        if not git_origin or not is_url_valid(git_origin):
            raise CommandException("You must specify a valid url")

        os.system(f"chezmoi init --apply --verbose {git_origin}")
else:
    warn_console.print("chezmoi not found. If you have already installed it, open a new terminal or refresh the environment variables")
