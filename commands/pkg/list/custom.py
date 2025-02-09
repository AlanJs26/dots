"""
ARCHDOTS
help: all custom packages
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

from rich import print
from archdots.package_manager import Custom
from archdots.settings import read_config

packages = Custom().get_packages(ignore_platform=True)

config = read_config()
custom_config = []
if "pkgs" in config and "custom" in config["pkgs"]:
    custom_config = config["pkgs"]["custom"]


def print_aligned(key, value):
    print("[cyan]{: <20}[/]: [green]{}".format(key, value))


for pkg in packages:

    print_aligned("name", "[cyan]" + pkg.name)
    print_aligned("description", pkg.description)
    print_aligned("url", pkg.url)
    print_aligned("depends", "  ".join(pkg.depends))
    print_aligned("source", "  ".join(pkg.source))
    print_aligned("platform", pkg.platform)
    print_aligned("available_functions", "  ".join(pkg.available_functions))
    print_aligned(
        "status",
        "installed" if pkg.check(supress_output=True) else "[red]uninstalled",
    )
    print_aligned("managed", "yes" if pkg.name in custom_config else "[red]no")

    print()
