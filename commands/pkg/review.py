from pathlib import Path
import tty, termios, sys

from src.constants import MODULE_PATH
from src.package import get_packages
from src.package_manager import PackageManager, package_managers
from src.settings import read_config

from rich.live import Live
from rich.table import Table
from rich.console import Group
from rich.panel import Panel


def getchar():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    tty.setraw(sys.stdin.fileno())
    ch = sys.stdin.read(1)
    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    # Exit on ctrl-c, ctrl-d, ctrl-z, or ESC
    if ord(ch) in [3, 4, 26, 27]:
        return ""
    return ch


config = read_config()

packages_by_pm: dict[PackageManager | str, list[str]] = {
    pm: pm.get_installed() for pm in package_managers
}


custom_packages = get_packages(str(Path(MODULE_PATH) / "packages"))

packages_by_pm["custom"] = [
    pkg.name for pkg in custom_packages if pkg.check(supress_output=True)
]

unmanaged_packages: dict[str, list[str]] = {}
for pm in config["pkgs"]:
    if pm not in packages_by_pm:
        continue
    unmanaged_packages[pm] = list(set(packages_by_pm[pm]) - set(config["pkgs"][pm]))


table = Table()
table.add_column()
table.add_column()

panel = Panel("minha nossa", style="blue", expand=False)

group = Group(table, panel)


print(unmanaged_packages)
exit()
for pm, packages in unmanaged_packages.items():
    for package in packages:
        table.add_row(f"{package} [blue]- {pm}", "[grey50]unreviewed")


def make_option(name: str, color="green"):
    return f"([{color}]{name[0]}[/]){name[1:]}"


decisions = ["add", "delete", "skip", "undo", "quit"]

with Live(group, auto_refresh=False) as live:  # update 4 times a second to feel fluid
    for row in range(1):
        choice = getchar()

        panel.title = str(row)
        panel.renderable = "[white]" + "  ".join(
            make_option(decision) for decision in decisions
        )
        table.add_row(f"{row}", f"description {choice}")
        live.refresh()
