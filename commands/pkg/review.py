"""
ARCHDOTS
help: opens a cli to decide what to do with unmanaged packages. add, uninstall or skip
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

from enum import Enum
import itertools
import tty, termios, sys
from typing import NamedTuple
from math import ceil

from archdots.package_manager import Custom, PackageManager, package_managers
from archdots.settings import read_config, save_config

from rich.live import Live
from rich.table import Table
from rich.console import Group
from rich.panel import Panel
from rich import print
from rich.console import Console
from rich.prompt import Confirm

warning_console = Console(style="yellow italic", stderr=True)

VISIBLE_ROWS = 10


def window[T](seq: list[T], n: int, window_size: int) -> list[T]:
    "Returns a sliding window (of width n) over data from the iterable"
    "   s -> (s0,s1,...s[n-1]), (s1,s2,...,sn), ...                   "
    return seq[n : n + window_size]


class Decision(Enum):
    ADD = "add"
    UNINSTALL = "uninstall"
    SKIP = "skip"
    BACK = "back"
    QUIT = "quit"
    FORWARD = "forward"
    INVALID = ""

    @staticmethod
    def handle(choice: str):
        if not choice:
            raise KeyboardInterrupt
        if ord(choice) == 127 or choice == "k":
            return Decision.BACK
        if choice == "j":
            return Decision.FORWARD
        for decision in Decision:
            if decision != Decision.INVALID and choice == decision.value[0]:
                return decision
        return Decision.INVALID


class Status(Enum):
    UNREVIEWED = "unreviewed"
    UNINSTALLED = "uninstall"
    ADDED = "add"
    SKIPPED = "skipped"


class Row(NamedTuple):
    pm: str
    pkg: str
    status: Status


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


packages_by_pm = {pm.name: pm.get_installed() for pm in package_managers}
pm_by_name: dict[str, PackageManager] = {pm.name: pm for pm in package_managers}

config = read_config()

if "pkgs" not in config:
    print("there is no pkgs configured", file=sys.stderr)
    exit()

unmanaged_packages: dict[str, list[str]] = {}
for pm in config["pkgs"]:
    if pm not in packages_by_pm:
        continue
    unmanaged_packages[pm] = list(set(packages_by_pm[pm]) - set(config["pkgs"][pm]))

if not unmanaged_packages:
    print("there are any unmanaged packages")
    exit()

rows: list[Row] = []
for pm, packages in unmanaged_packages.items():
    for package in packages:
        rows.append(Row(pm, package, Status.UNREVIEWED))
rows.sort(key=lambda r: r.pkg)

lost_packages = set(pkg.name for pkg in Custom().get_packages(True)).difference(
    Custom().get_installed(True)
)
if "custom" in config["pkgs"]:
    lost_packages = lost_packages.difference(config["pkgs"]["custom"])

if not rows:
    if lost_packages:
        warning_console.print(
            "Found packages that have been configured but aren't installed neither listed in config.yaml",
            "To remove this warning, delete those packages or add them to config.yaml\n",
            f'packages: {", ".join(lost_packages)}',
            sep="\n",
        )
    else:
        print("nothing to review")

    exit()


def generate_table(rows: list[Row], index=0, visible_rows=-1) -> Table:
    table = Table(show_header=False)
    table.add_column()
    table.add_column()
    table.add_column()

    if visible_rows <= 0 or len(rows) < VISIBLE_ROWS:
        visible_rows = len(rows)

    focused_index = index
    if index < ceil(visible_rows / 2):
        index = 0
    elif index > len(rows) - ceil(visible_rows / 2):
        focused_index = index - (len(rows) - visible_rows)
        index = len(rows) - visible_rows
    else:
        index = index - ceil(visible_rows / 2)
        focused_index = ceil(visible_rows / 2)

    for i, row in enumerate(window(rows, index, visible_rows)):
        pm, package, status = row
        focused_color = "[orange1]" if i == focused_index else "[blue]"
        status_color = "[grey50]"
        match status:
            case Status.ADDED:
                status_color = "[green]"
            case Status.UNINSTALLED:
                status_color = "[red]"
            case Status.SKIPPED:
                status_color = "[yellow]"
        table.add_row(
            focused_color + package, focused_color + pm, status_color + status.value
        )

    return table


table = generate_table(rows, visible_rows=VISIBLE_ROWS)
panel = Panel("", style="blue", expand=False)
group = Group(table, panel)


def make_option(name: str, color="green"):
    return f"([{color}]{name[0]}[/]){name[1:]}"


rows = rows[:11]

row_index = 0
with Live(
    group, auto_refresh=False, vertical_overflow="visible", transient=True
) as live:  # update 4 times a second to feel fluid
    while row_index < len(rows):
        row = rows[row_index]

        panel.title = row.pkg
        panel.renderable = "[white]" + "  ".join(
            make_option(decision)
            for decision in [
                d.value
                for d in list(Decision)
                if d not in [Decision.INVALID, Decision.FORWARD]
            ]
        )

        live.refresh()

        choice = Decision.handle(getchar())

        match (choice):
            case Decision.ADD:
                rows[row_index] = Row(row.pm, row.pkg, Status.ADDED)
            case Decision.UNINSTALL:
                rows[row_index] = Row(row.pm, row.pkg, Status.UNINSTALLED)
            case Decision.SKIP:
                rows[row_index] = Row(row.pm, row.pkg, Status.SKIPPED)
            case Decision.BACK:
                row_index = max(row_index - 1, 0)
                group.renderables[0] = generate_table(rows, row_index, VISIBLE_ROWS)
                continue
            case Decision.QUIT:
                exit()
            case Decision.INVALID:
                if row.status == Status.UNREVIEWED:
                    continue
            case Decision.FORWARD:
                if row.status == Status.UNREVIEWED:
                    rows[row_index] = Row(row.pm, row.pkg, Status.SKIPPED)

        row_index += 1
        group.renderables[0] = generate_table(rows, row_index, VISIBLE_ROWS)


error_happened = False
packages_to_uninstall = list(filter(lambda row: row.status == Status.UNINSTALLED, rows))

if packages_to_uninstall:
    print(
        f'[cyan]::[/] about to uninstall the following packages: [cyan]{"  ".join(f"{row.pm}:{row.pkg}" for row in packages_to_uninstall)}'
    )
    if Confirm.ask("[cyan]::[/] Proceed?", default=True):
        for pm_name, grouped_rows in itertools.groupby(
            packages_to_uninstall, lambda row: row.pm
        ):
            pkgs = [row.pkg for row in grouped_rows]
            error_happened = not pm_by_name[pm_name].uninstall(pkgs) or error_happened

packages_to_add = list(filter(lambda row: row.status == Status.ADDED, rows))
for pm_name, grouped_rows in itertools.groupby(packages_to_add, lambda row: row.pm):
    pkgs = [row.pkg for row in grouped_rows]
    config["pkgs"][pm_name].extend(pkgs)

    save_config(config)

if packages_to_uninstall:
    print(f"[red]{len(packages_to_uninstall)} packages uninstalled")
if packages_to_add:
    print(f"[green]{len(packages_to_add)} packages added")

if error_happened:
    warning_console.print(
        f"\nSome packages exited with error on removal. Possibly the numbers above are not valid"
    )


if lost_packages:
    warning_console.print(
        "\nFound packages that have been configured but aren't installed neither listed in config.yaml",
        "To remove this warning, delete those packages or add them to config.yaml\n",
        f'packages: {", ".join(lost_packages)}',
        sep="\n",
    )
