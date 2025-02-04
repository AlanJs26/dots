"""
ARCHDOTS
help: show status of files and packages
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

from rich import print
from archdots.package_manager import package_managers, Custom
from archdots.settings import read_config

installed_pkgs_by_pm = {pm.name: pm.get_installed() for pm in package_managers}

custom_pkg_names = [pkg.name for pkg in Custom().get_packages(use_memo=True)]

config = read_config()

if "pkgs" not in config:
    config["pkgs"] = {}

all_obscured_packages: list[str] = []

unmanaged_packages = 0
managed_packages = 0
pending_packages = 0
lost_packages = 0
for pm_name in installed_pkgs_by_pm:
    if pm_name not in config["pkgs"]:
        config["pkgs"][pm_name] = []
    managed_packages += len(
        set(installed_pkgs_by_pm[pm_name]).intersection(config["pkgs"][pm_name])
    )

    unmanaged_packages += len(
        set(installed_pkgs_by_pm[pm_name]) - set(config["pkgs"][pm_name])
    )

    obscured_packages = set()
    if pm_name != Custom().name:
        obscured_packages = set(custom_pkg_names).intersection(config["pkgs"][pm_name])
        all_obscured_packages.extend(f"{pm_name}:{pkg}" for pkg in obscured_packages)

    pending_packages += len(
        set(config["pkgs"][pm_name])
        - set(installed_pkgs_by_pm[pm_name])
        - obscured_packages
    )

lost_packages_set = set(pkg.name for pkg in Custom().get_packages(True)).difference(
    Custom().get_installed(True)
)
if "pkgs" in config and "custom" in config["pkgs"]:
    lost_packages_set = lost_packages_set.difference(config["pkgs"]["custom"])
lost_packages = len(lost_packages_set)


print("[cyan]::[/] Packages")


def print_aligned(key, value):
    print("[cyan]{: <10}[/]: [green]{}".format(key, value))


print_aligned("managed", managed_packages)
print_aligned("unmanaged", unmanaged_packages)
print_aligned("pending", pending_packages)
print_aligned("lost", lost_packages)
