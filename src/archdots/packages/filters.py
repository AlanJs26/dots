"""Package filtering helpers (managed, unmanaged, pending)."""

import fnmatch
import re
from typing import Any

from archdots.packages.managers.base import PackageManager
from archdots.packages.managers import Custom
from archdots.packages.managers.registry import get_package_managers
from archdots.config.manager import ConfigManager
from archdots.ui.console import warn_console


_WARNED_CONFLICTS: set[tuple[str, str, str]] = set()
_WARNED_INVALID_REGEX: set[str] = set()


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

    package_managers = get_package_managers()
    installed_pkgs_by_pm = {pm: pm.get_installed(use_memo) for pm in package_managers}

    unmanaged_packages: dict[PackageManager, list[str]] = {}
    for pm in installed_pkgs_by_pm:
        configured_pkgs = _normalize_pm_list(config, "pkgs", pm.name)
        pkgs = _sorted_unique(list(set(installed_pkgs_by_pm[pm]) - set(configured_pkgs)))
        unmanaged_packages[pm] = [
            pkg_name
            for pkg_name in pkgs
            if not is_package_ignored(config, pm.name, pkg_name)
        ]

    return unmanaged_packages


def get_managed_packages(use_memo=True) -> dict[PackageManager, list[str]]:
    config = ConfigManager().load(use_cache=use_memo)
    warn_pkg_ignored_conflicts(config)

    package_managers = get_package_managers()
    installed_pkgs_by_pm = {pm: pm.get_installed(use_memo) for pm in package_managers}

    installed_packages: dict[PackageManager, list[str]] = {}
    for pm in installed_pkgs_by_pm:
        configured_pkgs = _normalize_pm_list(config, "pkgs", pm.name)
        installed_packages[pm] = [
            pkg_name
            for pkg_name in _sorted_unique(installed_pkgs_by_pm[pm])
            if pkg_name in configured_pkgs
            and not is_package_ignored(config, pm.name, pkg_name)
        ]
    return installed_packages


def get_pending_packages(use_memo=True) -> dict[PackageManager, list[str]]:
    config = ConfigManager().load(use_cache=use_memo)
    warn_pkg_ignored_conflicts(config)

    package_managers = get_package_managers()
    installed_pkgs_by_pm = {pm: pm.get_installed(use_memo) for pm in package_managers}
    custom_pkg_names = [pkg.name for pkg in Custom().get_packages(use_memo=use_memo)]
    custom_pm_name = Custom().name

    pending_packages: dict[PackageManager, list[str]] = {}
    for pm in installed_pkgs_by_pm:
        configured_pkgs = _normalize_pm_list(config, "pkgs", pm.name)

        obscured_packages: set[str] = set()
        if pm.name != custom_pm_name:
            obscured_packages = set(custom_pkg_names).intersection(configured_pkgs)

        pkgs = _sorted_unique(
            list(set(configured_pkgs) - set(installed_pkgs_by_pm[pm]) - obscured_packages)
        )
        pending_packages[pm] = pkgs

        pending_packages[pm] = [
            pkg_name
            for pkg_name in pending_packages[pm]
            if not is_package_ignored(config, pm.name, pkg_name)
        ]

    return pending_packages
