"""Custom exception classes for archdots."""

from typing import Any


class ParseException(Exception):
    """Exception raised during file parsing."""

    def __init__(self, message, file="") -> None:
        if file:
            message = f"{file}\n\n{message}"
        super().__init__(message)


class GuiException(Exception):
    """Exception raised by GUI components."""

    pass


class PackageException(Exception):
    """Exception raised during package operations."""

    def __init__(
        self, message: str, package: Any | None = None, pkg_name="", pkgbuild=""
    ) -> None:
        import re

        if package:
            pkg_name = package.name
            pkgbuild = package.pkgbuild
        if pkg_name:
            message = f"Exception for '{pkg_name}' package\n{pkgbuild}\n{message}"
        super().__init__(re.sub(r"^\s+", "", message, flags=re.MULTILINE))


class PackageManagerException(Exception):
    """Exception raised by package managers."""

    pass


class SettingsException(Exception):
    """Exception raised during settings operations."""

    pass


class CommandException(Exception):
    """Exception raised during command execution."""

    pass
