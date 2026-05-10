"""
ARCHDOTS
help: overview of files and packages
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

from rich import print
from archdots.packages.managers.health import Health
from archdots.ui.console import print_title
from archdots.packages.managers import Custom
from archdots.packages.managers.registry import get_package_managers
from archdots.packages.filters import (
    is_package_ignored,
    get_managed_packages,
    get_unmanaged_packages,
    get_pending_packages,
)
from archdots.config.manager import ConfigManager
import subprocess

from archdots.ui.progress import progress_decorator

package_managers = get_package_managers()
config = ConfigManager().load()


def run(text: str):
    process = subprocess.Popen(
        text,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
        shell=True,
        text=True,
        encoding="cp437",
    )
    stdout, _ = process.communicate()
    return stdout


managed_packages = sum(len(pkgs) for pkgs in get_managed_packages().values())
unmanaged_packages = sum(len(pkgs) for pkgs in get_unmanaged_packages().values())
pending_packages = sum(len(pkgs) for pkgs in get_pending_packages().values())

ignored_packages = 0
for pm in package_managers:
    if pm.name == "health":
        continue
    installed = set(pm.get_installed(use_memo=True))
    configured = set(config.get("pkgs", {}).get(pm.name, []))

    obscured = set()
    if pm.name != "custom":
        obscured = set(pkg.name for pkg in Custom().get_packages(True)).intersection(
            configured
        )

    pending = configured - installed - obscured

    for pkg in installed.union(pending):
        if is_package_ignored(config, pm.name, pkg):
            ignored_packages += 1

lost_candidates = (
    set(pkg.name for pkg in Custom().get_packages(True))
    .difference(Custom().get_installed(True))
    .difference(config.get("pkgs", {}).get("custom", []))
)

lost_packages = 0
for pkg in lost_candidates:
    if is_package_ignored(config, "custom", pkg):
        ignored_packages += 1
    else:
        lost_packages += 1


@progress_decorator("health scripts")
def get_health_scripts():
    pkgs = Health().get_packages()
    return pkgs, [
        pkg for pkg in pkgs if not pkg.check(supress_output=True)
    ]


health_scripts, unconfigured_scripts = get_health_scripts()

print_title("Packages")


def print_aligned(key, value):
    print("[cyan]{: <11}[/]: [green]{}".format(key, value))


print_aligned("managed", managed_packages)
print_aligned("unmanaged", unmanaged_packages)
print_aligned("pending", pending_packages)
print_aligned("lost", lost_packages)
print_aligned("ignored", ignored_packages)

stdout = run("chezmoi managed")
managed_files = len(stdout.splitlines())

import re

git_stdout = run("chezmoi git -- diff --cached --name-only")
from_git = [
    line.strip().replace("dot_", ".").replace("private_", "").replace("executable_", "")
    for line in git_stdout.splitlines()
    if line.strip()
]

chezmoi_stdout = run("chezmoi diff")
from_chezmoi = re.findall(r"diff --git a/(.+?) b/", chezmoi_stdout)

pending_files = len(set(from_git + from_chezmoi))


print("\n[cyan]::[/] Files")
print_aligned("managed", managed_files)
print_aligned("pending", pending_files)

print("\n[cyan]::[/] Health")
print_aligned("configured", len(health_scripts) - len(unconfigured_scripts))
print_aligned("pending", len(unconfigured_scripts))
