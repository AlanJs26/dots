"""Package manager registry and utilities (__init__)."""

from archdots.packages.managers.apt import Apt
from archdots.packages.managers.base import PackageManager
from archdots.packages.managers.custom import Custom
from archdots.packages.managers.health import Health
from archdots.packages.managers.pacman import Pacman
from archdots.packages.managers.scoop import Scoop
from archdots.packages.managers.npm import Npm
from archdots.packages.managers.winget import Winget, WingetResultItem
from archdots.packages.managers.registry import (
    clear_package_managers_cache,
    get_package_managers,
    register_package_manager,
)

__all__ = [
    "PackageManager",
    "Apt",
    "Custom",
    "Health",
    "Pacman",
    "Winget",
    "Scoop",
    "Npm",
    "WingetResultItem",
    "get_package_managers",
    "register_package_manager",
    "clear_package_managers_cache",
]
