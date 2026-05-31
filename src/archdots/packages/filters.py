"""Package filtering helpers (managed, unmanaged, pending)."""

import fnmatch
import re
from typing import Any

from archdots.packages.managers.base import PackageManager
from archdots.packages.managers import Custom, Health
from archdots.packages.managers.registry import get_package_managers
from archdots.config.manager import ConfigManager
from archdots.ui.console import warn_console
from archdots.packages.status import bulk_get_installed


_WARNED_CONFLICTS: set[tuple[str, str, str]] = set()
_WARNED_INVALID_REGEX: set[str] = set()

_IGNORED_PMS = [Health().name]

def _match_pattern(pkg_name: str, pattern: str) -> bool:
    if pattern.startswith("re:"):
        regex = pattern[3:]
        try:
            return re.search(regex, pkg_name) is not None
        except re.error as err:
            if pattern not in _WARNED_INVALID_REGEX:
                _WARNED_INVALID_REGEX.add(pattern)
                warn_console.print(
                    f"warning: invalid ignored_pkgs regex '{pattern}': {err}"
                )
            return False
    if pattern.startswith("glob:"):
        return fnmatch.fnmatch(pkg_name, pattern[5:])
    return pkg_name == pattern


def _normalize_pm_list(config: dict[Any, Any], key: str, pm_name: str) -> list[str]:
    pm_map = config.get(key)
    if not isinstance(pm_map, dict):
        return []
    pm_values = pm_map.get(pm_name)
    if not isinstance(pm_values, list):
        return []
    return [value for value in pm_values if isinstance(value, str)]


def is_package_ignored(config: dict[Any, Any], pm_name: str, pkg_name: str) -> bool:
    patterns = _normalize_pm_list(config, "ignored_pkgs", pm_name)
    return any(_match_pattern(pkg_name, pattern) for pattern in patterns)


def warn_pkg_ignored_conflicts(config: dict[Any, Any]) -> None:
    pm_pkgs = config.get("pkgs")
    pm_ignored = config.get("ignored_pkgs")
    if not isinstance(pm_pkgs, dict) or not isinstance(pm_ignored, dict):
        return

    conflicts: set[tuple[str, str, str]] = set()
    for pm_name, pkgs in pm_pkgs.items():
        if not isinstance(pm_name, str) or not isinstance(pkgs, list):
            continue

        declared_pkgs = [pkg for pkg in pkgs if isinstance(pkg, str)]
        patterns = _normalize_pm_list(config, "ignored_pkgs", pm_name)

        for pkg in declared_pkgs:
            for pattern in patterns:
                if _match_pattern(pkg, pattern):
                    conflicts.add((pm_name, pkg, pattern))

    new_conflicts = sorted(conflicts - _WARNED_CONFLICTS)
    if not new_conflicts:
        return

    _WARNED_CONFLICTS.update(new_conflicts)

    warn_console.print("warning: pkgs x ignored_pkgs conflicts found (ignored_pkgs wins):")
    for pm_name, pkg, pattern in new_conflicts:
        warn_console.print(f" - {pm_name}:{pkg} matched by ignored pattern '{pattern}'")


def _sorted_unique(values: list[str]) -> list[str]:
    return sorted(set(values))


def get_unmanaged_packages(use_memo=True) -> dict[PackageManager, list[str]]:
    config = ConfigManager().load(use_cache=use_memo)
    warn_pkg_ignored_conflicts(config)

    package_managers = [pm for pm in get_package_managers() if pm.name not in _IGNORED_PMS]
    installed_data = bulk_get_installed(package_managers, use_memo, by_user=True)

    unmanaged_packages: dict[PackageManager, list[str]] = {}
    for pm in package_managers:
        installed_pkgs = installed_data.get(pm.name, [])
        configured_pkgs = _normalize_pm_list(config, "pkgs", pm.name)
        
        if pm.name == "deb":
            unmanaged_list = []
        else:
            unmanaged_list = [
                pkg_name
                for pkg_name in installed_pkgs
                if not pm.is_managed(pkg_name, configured_pkgs)
                and not is_package_ignored(config, pm.name, pkg_name)
            ]
        unmanaged_packages[pm] = _sorted_unique(unmanaged_list)

    return unmanaged_packages


def get_managed_packages(use_memo=True) -> dict[PackageManager, list[str]]:
    config = ConfigManager().load(use_cache=use_memo)
    warn_pkg_ignored_conflicts(config)

    package_managers = [pm for pm in get_package_managers() if pm.name not in _IGNORED_PMS]
    installed_data = bulk_get_installed(package_managers, use_memo, by_user=True)

    managed_packages: dict[PackageManager, list[str]] = {}
    for pm in package_managers:
        installed_pkgs = installed_data.get(pm.name, [])
        configured_pkgs = _normalize_pm_list(config, "pkgs", pm.name)
        managed_list = [
            pkg_name
            for pkg_name in installed_pkgs
            if pm.is_managed(pkg_name, configured_pkgs)
            and not is_package_ignored(config, pm.name, pkg_name)
        ]
        managed_packages[pm] = _sorted_unique(managed_list)
    return managed_packages


def get_pending_packages(use_memo=True) -> dict[PackageManager, list[str]]:
    config = ConfigManager().load(use_cache=use_memo)
    warn_pkg_ignored_conflicts(config)

    package_managers = [pm for pm in get_package_managers() if pm.name not in _IGNORED_PMS]
    # For pending, we need raw data (by_user=False) to correctly detect installed aliases
    installed_data_raw = bulk_get_installed(package_managers, use_memo, by_user=False)
    
    custom_pkg_names = [pkg.name for pkg in Custom().get_packages(use_memo=use_memo)]
    custom_pm_name = Custom().name

    pending_packages: dict[PackageManager, list[str]] = {}
    
    all_custom_pkg_names = [pkg.name for pkg in Custom().get_packages(use_memo=use_memo, ignore_platform=True)]
    unsupported_custom = set(all_custom_pkg_names) - set(custom_pkg_names)
    
    for pm in package_managers:
        installed_pkgs_raw = installed_data_raw.get(pm.name, [])
        configured_pkgs = _normalize_pm_list(config, "pkgs", pm.name)
        
        if pm.name == custom_pm_name:
            configured_pkgs = [p for p in configured_pkgs if p not in unsupported_custom]

        ignored_by_pm = pm.get_ignored_packages(use_memo=use_memo)

        pkgs = [
            pkg_name
            for pkg_name in configured_pkgs
            if not pm.is_installed_in_data(pkg_name, installed_pkgs_raw)
            and pkg_name not in ignored_by_pm
            and not is_package_ignored(config, pm.name, pkg_name)
        ]
        pending_packages[pm] = _sorted_unique(pkgs)

    return pending_packages
