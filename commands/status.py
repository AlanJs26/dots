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


# Fetch all data in parallel batches to avoid redundant discovery and duplicate bars
package_managers_to_check = [pm for pm in package_managers if pm.name != "health"]
# 1. Fetch raw data (for accurate pending checks) and filtered data (for counting) in parallel
from archdots.packages.status import bulk_get_installed
installed_raw_data = bulk_get_installed(package_managers_to_check, use_memo=True, by_user=False)
installed_filtered_data = bulk_get_installed(package_managers_to_check, use_memo=True, by_user=True)

# 2. Get custom packages once
custom_manager = Custom()
custom_packages_all = custom_manager.get_packages(use_memo=True, ignore_platform=True)
custom_packages_supported = custom_manager.get_packages(use_memo=True)

custom_pkg_names_all = [pkg.name for pkg in custom_packages_all]
custom_pkg_names_supported = [pkg.name for pkg in custom_packages_supported]
unsupported_custom = set(custom_pkg_names_all) - set(custom_pkg_names_supported)

managed_packages = 0
unmanaged_packages = 0
pending_packages = 0
ignored_packages = 0

from archdots.packages.filters import _normalize_pm_list

for pm in package_managers_to_check:
    installed_raw = installed_raw_data.get(pm.name, [])
    installed_filtered = installed_filtered_data.get(pm.name, [])
    
    configured_list = _normalize_pm_list(config, "pkgs", pm.name)
    configured = set(configured_list)
    
    if pm.name == "custom":
        configured -= unsupported_custom

    obscured = set()
    if pm.name != "custom":
        obscured = set(custom_pkg_names_supported).intersection(configured)

    # Calculate Pending
    pending_list = [p for p in configured if not pm.is_installed_in_data(p, installed_raw) and p not in obscured]
    
    # Managed / Unmanaged (using filtered list to avoid version duplicates)
    for p in installed_filtered:
        if is_package_ignored(config, pm.name, p):
            ignored_packages += 1
            continue
        if pm.is_managed(p, configured_list):
            managed_packages += 1
        else:
            unmanaged_packages += 1
            
    for p in pending_list:
        if is_package_ignored(config, pm.name, p):
            ignored_packages += 1
        else:
            pending_packages += 1

# Lost candidates: supported custom packages that are neither installed nor in config
custom_installed = set(installed_raw_data.get("custom", []))
custom_configured = set(_normalize_pm_list(config, "pkgs", "custom"))

lost_candidates = (
    set(custom_pkg_names_supported)
    .difference(custom_installed)
    .difference(custom_configured)
)

lost_packages = 0
for pkg in lost_candidates:
    if is_package_ignored(config, "custom", pkg):
        ignored_packages += 1
    else:
        lost_packages += 1

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
