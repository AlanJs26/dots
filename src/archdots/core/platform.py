"""Platform detection utilities."""

import os


def is_windows() -> bool:
    """Check if running on Windows."""
    return os.name == "nt"


def is_linux() -> bool:
    """Check if running on Linux."""
    return os.name != "nt"


def get_platform() -> str:
    """Return 'windows' or 'linux'."""
    return "windows" if is_windows() else "linux"
