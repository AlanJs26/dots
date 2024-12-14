"""
ARCHDOTS
help: list installed packages
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

from src.package import get_packages
from pathlib import Path
from rich import print

import src

sitepackage_folder = Path(list(src.__path__)[0]).parent

custom_packages = get_packages(str(sitepackage_folder / "packages"))
print(custom_packages)
