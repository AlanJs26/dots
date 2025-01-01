from archdots.package_manager import PackageManager, package_managers
from archdots.settings import read_config


def get_unmanaged_packages(use_memo=True) -> dict[PackageManager, list[str]]:
    config = read_config()
    installed_pkgs_by_pm = {pm: pm.get_installed(use_memo) for pm in package_managers}

    unmanaged_packages: dict[PackageManager, list[str]] = {}
    for pm in installed_pkgs_by_pm:
        if pm.name not in config["pkgs"]:
            config["pkgs"][pm.name] = []
        pkgs = list(set(installed_pkgs_by_pm[pm]) - set(config["pkgs"][pm.name]))

        unmanaged_packages[pm] = pkgs

    return unmanaged_packages


def get_managed_packages(use_memo=True) -> dict[PackageManager, list[str]]:
    config = read_config()
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
    config = read_config()
    if "pkgs" not in config:
        return {}
    installed_pkgs_by_pm = {pm: pm.get_installed(use_memo) for pm in package_managers}

    pending_packages: dict[PackageManager, list[str]] = {}
    for pm in installed_pkgs_by_pm:
        if pm.name not in config["pkgs"]:
            continue
        pkgs = list(set(config["pkgs"][pm.name]) - set(installed_pkgs_by_pm[pm]))

        pending_packages[pm] = pkgs

    return pending_packages
