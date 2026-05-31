"""
ARCHDOTS
help: opens a tui to decide what to do with unmanaged, pending and lost packages
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

from enum import Enum
import itertools
import shutil

from typing import NamedTuple
from math import ceil
from pathlib import Path

from archdots.core.constants import PACKAGES_FOLDER, PLATFORM
from archdots.packages.managers import Custom, PackageManager
from archdots.packages.managers.registry import get_package_managers
from archdots.packages.filters import (
    is_package_ignored,
    warn_pkg_ignored_conflicts,
    get_unmanaged_packages,
    get_pending_packages,
)
from archdots.config.manager import ConfigManager
from archdots.ui.console import print_title, title, warn_console, confirm

from rich.live import Live
from rich.table import Table
from rich.console import Group
from rich.panel import Panel
from rich import print
from archdots.core.platforms.registry import get_current_platform


class _Getch:
    """Gets a single character from standard input.  Does not echo to the
    screen."""

    def __init__(self):
        if get_current_platform().supports("linux"):
            self.impl = _GetchUnix()
        else:
            self.impl = _GetchWindows()

    def __call__(self):
        ch = self.impl()

        if isinstance(ch, bytes):
            # Map Windows extended keys to existing navigation keys.
            # msvcrt returns b'\xe0' or b'\x00' then a second byte for arrows.
            if ch in (b"\xe0", b"\x00"):
                return ""

            if ch == b"P":
                return "j"  # down arrow
            if ch == b"H":
                return "k"  # up arrow

            ch = ch.decode("latin-1", errors="ignore")

        if not ch:
            return ""

        if ord(ch) in [3, 4, 26, 27]:
            return ""
        return str(ch)


class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)  # type: ignore
        try:
            tty.setraw(sys.stdin.fileno())  # type: ignore
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)  # type: ignore
        return ch


class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt

        first = msvcrt.getch()
        if first in (b"\xe0", b"\x00"):
            # Return the second byte of extended key sequences (arrows, etc.).
            return msvcrt.getch()
        return first


getchar = _Getch()


VISIBLE_ROWS = 10
package_managers = get_package_managers()


def window[T](seq: list[T], n: int, window_size: int) -> list[T]:
    "Returns a sliding window (of width n) over data from the iterable"
    "   s -> (s0,s1,...s[n-1]), (s1,s2,...,sn), ...                   "
    return seq[n : n + window_size]


class Decision(Enum):
    ADD = "add"
    UNINSTALL = "uninstall"
    IGNORE = "ignore"
    INSTALL = "install"
    DELETE = "delete"
    SKIP = "skip"
    BACK = "back"
    QUIT = "quit"
    FORWARD = "forward"
    INVALID = ""

    @staticmethod
    def handle(choice: str, allowed_decisions: list["Decision"]):
        if not choice:
            raise KeyboardInterrupt
        if choice == "q":
            return Decision.QUIT
        if ord(choice) == 127 or choice == "k":
            return Decision.BACK
        if choice == "j":
            return Decision.FORWARD

        for decision in allowed_decisions:
            if choice == decision.value[0]:
                return decision

        return Decision.INVALID


class Status(Enum):
    UNREVIEWED = "unreviewed"
    UNINSTALLED = "uninstall"
    ADDED = "add"
    IGNORED = "ignored"
    INSTALLED = "install"
    DELETED = "delete"
    SKIPPED = "skipped"


class Kind(Enum):
    UNMANAGED = "unmanaged"
    PENDING = "pending"
    LOST = "lost"


class Row(NamedTuple):
    kind: Kind
    pm: str
    pkg: str
    status: Status


pm_by_name: dict[str, PackageManager] = {pm.name: pm for pm in package_managers}

config = ConfigManager().load()

custom_pm_name = Custom().name
custom_pkg_names = [pkg.name for pkg in Custom().get_packages(use_memo=False)]

unmanaged_dict = get_unmanaged_packages()
pending_dict = get_pending_packages()

rows: list[Row] = []
for pm, packages in unmanaged_dict.items():
    for package in packages:
        rows.append(Row(Kind.UNMANAGED, pm.name, package, Status.UNREVIEWED))

for pm, packages in pending_dict.items():
    for package in packages:
        rows.append(Row(Kind.PENDING, pm.name, package, Status.UNREVIEWED))

lost_packages = set(custom_pkg_names).difference(Custom().get_installed(use_memo=True))
if "pkgs" in config and "custom" in config["pkgs"]:
    lost_packages = lost_packages.difference(config["pkgs"]["custom"])
lost_packages = {
    pkg
    for pkg in lost_packages
    if not is_package_ignored(config, custom_pm_name, pkg)
}

for package in sorted(lost_packages):
    rows.append(Row(Kind.LOST, custom_pm_name, package, Status.UNREVIEWED))

rows.sort(key=lambda r: (r.kind.value, r.pm, r.pkg))

if not rows:
    print("nothing to review")
    exit()


def generate_table(rows: list[Row], index=0, visible_rows=-1) -> Table:
    table = Table(show_header=False)
    table.add_column()
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
        kind, pm, package, status = row
        focused_color = "[orange1]" if i == focused_index else "[blue]"
        status_color = "[grey50]"
        kind_color = "[grey70]"
        match kind:
            case Kind.UNMANAGED:
                kind_color = "[cyan]"
            case Kind.PENDING:
                kind_color = "[yellow]"
            case Kind.LOST:
                kind_color = "[magenta]"

        match status:
            case Status.ADDED:
                status_color = "[green]"
            case Status.UNINSTALLED:
                status_color = "[red]"
            case Status.IGNORED:
                status_color = "[magenta]"
            case Status.INSTALLED:
                status_color = "[green]"
            case Status.DELETED:
                status_color = "[red]"
            case Status.SKIPPED:
                status_color = "[yellow]"
        table.add_row(
            focused_color + package,
            focused_color + pm,
            kind_color + kind.value,
            status_color + status.value,
        )

    return table


table = generate_table(rows, visible_rows=VISIBLE_ROWS)
panel = Panel("", style="blue", expand=False)
group = Group(table, panel)


def make_option(name: str, color="green"):
    return f"([{color}]{name[0]}[/]){name[1:]}"


def allowed_decisions_for(kind: Kind) -> list[Decision]:
    if kind == Kind.UNMANAGED:
        return [Decision.ADD, Decision.UNINSTALL, Decision.IGNORE, Decision.SKIP]
    if kind == Kind.PENDING:
        return [Decision.INSTALL, Decision.SKIP]
    return [Decision.DELETE, Decision.SKIP]


row_index = 0
with Live(
    group, auto_refresh=False, vertical_overflow="visible", transient=True
) as live:  # update 4 times a second to feel fluid
    while row_index < len(rows):
        row = rows[row_index]
        kind, _, _, _ = row
        row_actions = allowed_decisions_for(kind)

        panel.title = row.pkg
        panel.renderable = "[white]" + "  ".join(
            make_option(decision.value)
            for decision in [*row_actions, Decision.QUIT]
        )

        live.refresh()

        choice = Decision.handle(getchar(), row_actions)

        match (choice):
            case Decision.ADD:
                rows[row_index] = Row(row.kind, row.pm, row.pkg, Status.ADDED)
            case Decision.UNINSTALL:
                rows[row_index] = Row(row.kind, row.pm, row.pkg, Status.UNINSTALLED)
            case Decision.IGNORE:
                rows[row_index] = Row(row.kind, row.pm, row.pkg, Status.IGNORED)
            case Decision.INSTALL:
                rows[row_index] = Row(row.kind, row.pm, row.pkg, Status.INSTALLED)
            case Decision.DELETE:
                rows[row_index] = Row(row.kind, row.pm, row.pkg, Status.DELETED)
            case Decision.SKIP:
                rows[row_index] = Row(row.kind, row.pm, row.pkg, Status.SKIPPED)
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
                    rows[row_index] = Row(row.kind, row.pm, row.pkg, Status.SKIPPED)

        row_index += 1
        group.renderables[0] = generate_table(rows, row_index, VISIBLE_ROWS)


error_happened = False
unmanaged_rows = [row for row in rows if row.kind == Kind.UNMANAGED]
pending_rows = [row for row in rows if row.kind == Kind.PENDING]
lost_rows = [row for row in rows if row.kind == Kind.LOST]

packages_to_uninstall = [row for row in unmanaged_rows if row.status == Status.UNINSTALLED]

if packages_to_uninstall:
    print_title(
        f'about to uninstall the following packages: [cyan]{"  ".join(f"{row.pm}:{row.pkg}" for row in packages_to_uninstall)}'
    )
    if confirm("Proceed?", default=True):
        for pm_name, grouped_rows in itertools.groupby(
            packages_to_uninstall, lambda row: row.pm
        ):
            pkgs = [row.pkg for row in grouped_rows]
            error_happened = not pm_by_name[pm_name].uninstall(pkgs) or error_happened

packages_to_add = [row for row in unmanaged_rows if row.status == Status.ADDED]
packages_to_ignore = [row for row in unmanaged_rows if row.status == Status.IGNORED]
packages_to_install = [row for row in pending_rows if row.status == Status.INSTALLED]
packages_to_delete = [row for row in lost_rows if row.status == Status.DELETED]

if packages_to_install:
    print_title(
        f'about to install the following pending packages: [cyan]{"  ".join(f"{row.pm}:{row.pkg}" for row in packages_to_install)}'
    )
    if confirm("Proceed?", default=True):
        for pm_name, grouped_rows in itertools.groupby(
            packages_to_install, lambda row: row.pm
        ):
            pkgs = [row.pkg for row in grouped_rows]
            error_happened = not pm_by_name[pm_name].install(pkgs) or error_happened

if "pkgs" not in config:
    config["pkgs"] = {}

for pm_name, grouped_rows in itertools.groupby(packages_to_add, lambda row: row.pm):
    if pm_name not in config["pkgs"]:
        config["pkgs"][pm_name] = []
    pkgs = [row.pkg for row in grouped_rows]
    config["pkgs"][pm_name].extend(pkgs)
    config["pkgs"][pm_name] = sorted(set(config["pkgs"][pm_name]))

if "ignored_pkgs" not in config:
    config["ignored_pkgs"] = {}

for pm_name, grouped_rows in itertools.groupby(packages_to_ignore, lambda row: row.pm):
    if pm_name not in config["ignored_pkgs"]:
        config["ignored_pkgs"][pm_name] = []
    pkgs = [row.pkg for row in grouped_rows]
    config["ignored_pkgs"][pm_name].extend(pkgs)
    config["ignored_pkgs"][pm_name] = sorted(set(config["ignored_pkgs"][pm_name]))

if packages_to_delete:
    print_title(
        f'about to delete the following lost packages: [cyan]{"  ".join(row.pkg for row in packages_to_delete)}'
    )
    if confirm("Proceed?", default=True):
        for row in packages_to_delete:
            package_path = Path(PACKAGES_FOLDER) / row.pkg
            if package_path.is_dir():
                shutil.rmtree(package_path)

ConfigManager().save(config)

if packages_to_uninstall:
    print(f"[red]{len(packages_to_uninstall)} packages uninstalled")
if packages_to_add:
    print(f"[green]{len(packages_to_add)} packages added")
if packages_to_ignore:
    print(f"[magenta]{len(packages_to_ignore)} packages ignored")
if packages_to_install:
    print(f"[green]{len(packages_to_install)} pending packages installed")
if packages_to_delete:
    print(f"[red]{len(packages_to_delete)} lost packages deleted")

if error_happened:
    warn_console.print(
        f"\nSome packages exited with error on removal. Possibly the numbers above are not valid"
    )


