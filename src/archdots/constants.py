from pathlib import Path
import os
import archdots

match os.name:
    case "nt":
        PLATFORM = "windows"
        CACHE_FOLDER = os.path.expanduser("~/AppData/Local/Temp/archdots")
        CONFIG_FOLDER = os.path.expanduser("~/AppData/Local/archdots")
        CHEZMOI_FOLDER = os.path.expanduser("~/AppData/Local/chezmoi")
    case _:
        PLATFORM = "linux"
        CACHE_FOLDER = os.path.expanduser("~/.cache/archdots")
        CONFIG_FOLDER = os.path.expanduser("~/.config/archdots")
        CHEZMOI_FOLDER = os.path.expanduser("~/.local/share/chezmoi")

COMMANDS_FOLDER = os.path.join(CONFIG_FOLDER, "commands")
HEALTH_FOLDER = os.path.join(CONFIG_FOLDER, "health")
PACKAGES_FOLDER = os.path.join(CONFIG_FOLDER, "packages")


MODULE_PATH = str(Path(list(archdots.__path__)[0]).parent.parent)
