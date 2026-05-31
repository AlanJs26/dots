"""Package manager registry and discovery."""

from archdots.packages.managers.base import PackageManager

_package_managers: list[PackageManager] = []


def get_package_managers() -> list[PackageManager]:
    """Get all available package managers (custom, pacman, winget, scoop).
    
    Returns:
        List of available PackageManager instances on this system
    """
    global _package_managers

    if not _package_managers:
        from archdots.packages.managers.apt import Apt
        from archdots.packages.managers.custom import Custom
        from archdots.packages.managers.health import Health
        from archdots.packages.managers.pacman import Pacman
        from archdots.packages.managers.scoop import Scoop
        from archdots.packages.managers.npm import Npm
        from archdots.packages.managers.winget import Winget
        from archdots.packages.managers.uv import Uv

        _package_managers = [
            pm for pm in [Pacman(), Apt(), Npm(), Uv(), Custom(), Health(), Winget(), Scoop()] if pm.is_available()
        ]

    return _package_managers


def register_package_manager(manager: PackageManager) -> None:
    """Register a package manager.
    
    Args:
        manager: PackageManager instance to register
    """
    global _package_managers
    if manager not in _package_managers:
        _package_managers.append(manager)


def clear_package_managers_cache() -> None:
    global _package_managers
    _package_managers = []
