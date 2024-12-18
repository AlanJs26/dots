import os

CONFIG_FOLDER = os.path.expanduser("~/.config/archdots")
COMMANDS_FOLDER = "commands"
CACHE_FOLDER = os.path.expanduser("~/.cache/archdots")

from pathlib import Path
import src

MODULE_PATH = str(Path(list(src.__path__)[0]).parent)
