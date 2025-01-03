from typing import Any


class ParseException(Exception):
    def __init__(self, message, file="") -> None:

        if file:
            message = f"{file}\n\n{message}"
        super().__init__(message)


class GuiException(Exception):
    pass


class PackageException(Exception):
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
    pass


class SettingsException(Exception):
    pass


class CommandException(Exception):
    pass
