from pathlib import Path
import os
import src

CONFIG_FOLDER = os.path.expanduser("~/.config/archdots")

COMMANDS_FOLDER = os.path.join(CONFIG_FOLDER, "commands")
HEALTH_FOLDER = os.path.join(CONFIG_FOLDER, "health")
PACKAGES_FOLDER = os.path.join(CONFIG_FOLDER, "packages")

CACHE_FOLDER = os.path.expanduser("~/.cache/archdots")

MODULE_PATH = str(Path(list(src.__path__)[0]).parent)
CHEZMOI_FOLDER = os.path.expanduser("~/.local/share/chezmoi")
