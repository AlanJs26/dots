"""
ARCHDOTS
help: installed packages that aren't in config.yaml
flags:
    - long: --filter
      type: str
      nargs: +
      help: filter by one or more package managers
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

from rich import print
from archdots.ui.console import print_title
from archdots.packages.managers.registry import get_package_managers
from archdots.config.manager import ConfigManager

package_managers = get_package_managers()

installed_pkgs_by_pm = {pm.name: pm.get_installed() for pm in package_managers}

config = ConfigManager().load()


if "pkgs" not in config:
    config["pkgs"] = {}

unmanaged_packages: dict[str, list[str]] = {}
for pm_name in installed_pkgs_by_pm.keys():
    if pm_name not in config["pkgs"]:
        config["pkgs"][pm_name] = []
    unmanaged_packages[pm_name] = list(
        set(installed_pkgs_by_pm[pm_name]) - set(config["pkgs"][pm_name])
    )

for name, pkgs in unmanaged_packages.items():
    if not pkgs:
        continue
    if args["filter"] and name not in args["filter"]:
        continue
    print_title(f"{name}")
    for pkg_name in pkgs:
        print(pkg_name)


