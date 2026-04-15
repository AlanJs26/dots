"""
ARCHDOTS
help: overview of files and packages
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

from rich import print
from archdots.ui.console import print_title
from archdots.core.constants import HEALTH_FOLDER
from archdots.packages.package import get_packages
from archdots.packages.managers import Custom
from archdots.packages.managers.registry import get_package_managers
from archdots.packages.filters import is_package_ignored, warn_pkg_ignored_conflicts
from archdots.config.manager import ConfigManager
import subprocess

package_managers = get_package_managers()
installed_pkgs_by_pm = {pm.name: pm.get_installed() for pm in package_managers}

custom_pkg_names = [pkg.name for pkg in Custom().get_packages(use_memo=True)]
custom_pm_name = Custom().name

config = ConfigManager().load()
warn_pkg_ignored_conflicts(config)


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


if "pkgs" not in config:
    config["pkgs"] = {}

unmanaged_packages = 0
managed_packages = 0
pending_packages = 0
ignored_packages = 0
lost_packages = 0
for pm_name in installed_pkgs_by_pm:
    if pm_name not in config["pkgs"]:
        config["pkgs"][pm_name] = []
    installed_set = set(installed_pkgs_by_pm[pm_name])
    configured_set = set(config["pkgs"][pm_name])

    managed_set = installed_set.intersection(configured_set)
    unmanaged_set = installed_set - configured_set

    ignored_installed_set = {
        pkg for pkg in installed_set if is_package_ignored(config, pm_name, pkg)
    }

    managed_packages += len(managed_set - ignored_installed_set)
    unmanaged_packages += len(unmanaged_set - ignored_installed_set)

    obscured_packages = set()
    if pm_name != custom_pm_name:
        obscured_packages = set(custom_pkg_names).intersection(config["pkgs"][pm_name])

    pending_set = configured_set - installed_set - obscured_packages
    ignored_pending_set = {
        pkg for pkg in pending_set if is_package_ignored(config, pm_name, pkg)
    }
    pending_packages += len(pending_set - ignored_pending_set)

    ignored_packages += len(ignored_installed_set)
    ignored_packages += len(ignored_pending_set)

lost_candidates_set = set(pkg.name for pkg in Custom().get_packages(True)).difference(
    Custom().get_installed(True)
)
if "pkgs" in config and "custom" in config["pkgs"]:
    lost_candidates_set = lost_candidates_set.difference(config["pkgs"]["custom"])

ignored_lost_packages_set = {
    pkg
    for pkg in lost_candidates_set
    if is_package_ignored(config, custom_pm_name, pkg)
}

lost_packages_set = {
    pkg
    for pkg in lost_candidates_set
    if not is_package_ignored(config, custom_pm_name, pkg)
}
ignored_packages += len(ignored_lost_packages_set)

lost_packages = len(lost_packages_set)


health_scripts = get_packages(HEALTH_FOLDER)
unconfigured_scripts = [
    pkg for pkg in health_scripts if not pkg.check(supress_output=True)
]

print_title("Packages")


def print_aligned(key, value):
    print("[cyan]{: <10}[/]: [green]{}".format(key, value))


print_aligned("managed", managed_packages)
print_aligned("unmanaged", unmanaged_packages)
print_aligned("pending", pending_packages)
print_aligned("lost", lost_packages)
print_aligned("ignored", ignored_packages)

stdout = run("chezmoi managed")
managed_files = len(stdout.splitlines())

stdout = run(
    r"""
from_git="$(chezmoi git -- diff --cached --numstat | awk '{print $3}' | rg 'dot_' -r '.' --passthrough | sed 's/private_|executable_//g')"
from_chezmoi="$(chezmoi diff | rg 'diff --git' | rg 'a/(.+) b/' -o -r '$1')"

echo -e "$from_git\n$from_chezmoi" | awk NF | sort -u
    """
)
pending_files = len(stdout.splitlines())


print("[cyan]::[/] Files")
print_aligned("managed", managed_files)
print_aligned("pending", pending_files)


