"""
ARCHDOTS
help: all custom packages
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

from rich.console import Console
from rich.table import Table
from rich import box
from archdots.package_manager import Custom
from archdots.settings import read_config

packages = Custom().get_packages(ignore_platform=True)

console = Console()

config = read_config()
custom_config = []
if "pkgs" in config and "custom" in config["pkgs"]:
    custom_config = config["pkgs"]["custom"]

for pkg in packages:
    table = Table(
        show_header=False,
        box=box.MINIMAL,
        padding=(0, 0, 0, 1),
        show_edge=False,
        safe_box=True,
    )

    table.add_column(justify="left", style="cyan")
    table.add_column(justify="left", style="green")

    table.add_row("name", "[cyan]" + pkg.name)
    table.add_row("description", pkg.description)
    table.add_row("url", pkg.url)
    table.add_row("depends", "  ".join(pkg.depends))
    table.add_row("source", "  ".join(pkg.source))
    table.add_row("platform", pkg.platform)
    table.add_row("available_functions ", "  ".join(pkg.available_functions))
    table.add_row(
        "status ", "installed" if pkg.check(supress_output=True) else "[red]uninstalled"
    )
    table.add_row("managed ", "yes" if pkg.name in custom_config else "[red]no")

    console.print(table)

    console.print()
