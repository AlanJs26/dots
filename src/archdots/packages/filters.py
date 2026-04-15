"""Package filtering helpers (managed, unmanaged, pending)."""

from archdots.packages.managers.base import PackageManager
from archdots.packages.managers.registry import get_package_managers
from archdots.config.manager import ConfigManager


def get_unmanaged_packages(use_memo=True) -> dict[PackageManager, list[str]]:
    config = ConfigManager().load(use_cache=use_memo)
    package_managers = get_package_managers()
    installed_pkgs_by_pm = {pm: pm.get_installed(use_memo) for pm in package_managers}
    if "pkgs" not in config:
        config["pkgs"] = {}

    unmanaged_packages: dict[PackageManager, list[str]] = {}
    for pm in installed_pkgs_by_pm:
        if pm.name not in config["pkgs"]:
            config["pkgs"][pm.name] = []
        pkgs = list(set(installed_pkgs_by_pm[pm]) - set(config["pkgs"][pm.name]))
        unmanaged_packages[pm] = pkgs

    return unmanaged_packages


def get_managed_packages(use_memo=True) -> dict[PackageManager, list[str]]:
    config = ConfigManager().load(use_cache=use_memo)
    if "pkgs" not in config:
        return {}

    package_managers = get_package_managers()
    installed_pkgs_by_pm = {pm: pm.get_installed(use_memo) for pm in package_managers}

    installed_packages: dict[PackageManager, list[str]] = {}
    for pm in installed_pkgs_by_pm:
        if pm.name not in config["pkgs"]:
            continue
        installed_packages[pm] = [
            pkg_name
            for pkg_name in installed_pkgs_by_pm[pm]
            if pkg_name in config["pkgs"][pm.name]
        ]
    return installed_packages


def get_pending_packages(use_memo=True) -> dict[PackageManager, list[str]]:
    config = ConfigManager().load(use_cache=use_memo)
    if "pkgs" not in config:
        return {}

    package_managers = get_package_managers()
    installed_pkgs_by_pm = {pm: pm.get_installed(use_memo) for pm in package_managers}

    pending_packages: dict[PackageManager, list[str]] = {}
    for pm in installed_pkgs_by_pm:
        if pm.name not in config["pkgs"]:
            continue
        pkgs = list(set(config["pkgs"][pm.name]) - set(installed_pkgs_by_pm[pm]))
        pending_packages[pm] = pkgs

    return pending_packages
