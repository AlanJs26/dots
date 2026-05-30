"""Core constants: paths, platform, module locations."""

from pathlib import Path
import os
import archdots

# Platform detection
if os.name == "nt":
    PLATFORM = "windows"
    CACHE_FOLDER = os.path.expanduser("~/AppData/Local/Temp/archdots")
else:
    PLATFORM = "linux"
    CACHE_FOLDER = os.path.expanduser("~/.cache/archdots")

# Standard folders
CONFIG_FOLDER = os.path.expanduser("~/.config/archdots")
CHEZMOI_FOLDER = os.path.expanduser("~/.local/share/chezmoi")

# Config subfolders
COMMANDS_FOLDER = os.path.join(CONFIG_FOLDER, "commands")
HEALTH_FOLDER = os.path.join(CONFIG_FOLDER, "health")
PACKAGES_FOLDER = os.path.join(CONFIG_FOLDER, "packages")

# Module location
MODULE_PATH = str(Path(list(archdots.__path__)[0]).parent.parent)
