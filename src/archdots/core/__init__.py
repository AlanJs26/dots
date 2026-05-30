"""Core infrastructure: exceptions, constants, platform detection."""

from archdots.core.exceptions import (
    ParseException,
    GuiException,
    PackageException,
    PackageManagerException,
    SettingsException,
    CommandException,
)
from archdots.core.constants import (
    PLATFORM,
    CACHE_FOLDER,
    CONFIG_FOLDER,
    CHEZMOI_FOLDER,
    COMMANDS_FOLDER,
    HEALTH_FOLDER,
    PACKAGES_FOLDER,
    MODULE_PATH,
)
from archdots.core.platform import is_windows, is_linux

__all__ = [
    "ParseException",
    "GuiException",
    "PackageException",
    "PackageManagerException",
    "SettingsException",
    "CommandException",
    "PLATFORM",
    "CACHE_FOLDER",
    "CONFIG_FOLDER",
    "CHEZMOI_FOLDER",
    "COMMANDS_FOLDER",
    "HEALTH_FOLDER",
    "PACKAGES_FOLDER",
    "MODULE_PATH",
    "is_windows",
    "is_linux",
]
