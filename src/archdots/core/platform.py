"""Platform detection utilities."""

from archdots.core.platforms.registry import get_current_platform


def is_windows() -> bool:
    """Check if running on Windows or derivative."""
    return get_current_platform().supports("windows")


def is_linux() -> bool:
    """Check if running on Linux or derivative."""
    return get_current_platform().supports("linux")


def get_platform() -> str:
    """Return the active platform name (e.g. 'archlinux', 'ubuntu', 'windows')."""
    return get_current_platform().name
