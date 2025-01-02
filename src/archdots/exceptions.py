class ParseException(Exception):
    def __init__(self, message, file="") -> None:

        if file:
            message = f"{file}\n\n{message}"
        super().__init__(message)


class GuiException(Exception):
    pass


class PackageException(Exception):
    def __init__(self, message, pkg_name="") -> None:
        import re

        if pkg_name:
            message = f"Exception for '{pkg_name}' package\n{message}"
        super().__init__(re.sub(r"^\s+", "", message, flags=re.MULTILINE))


class PackageManagerException(Exception):
    pass


class SettingsException(Exception):
    pass


class CommandException(Exception):
    pass
