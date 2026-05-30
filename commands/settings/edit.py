from archdots.core.constants import CONFIG_FOLDER
from pathlib import Path

from archdots.config.manager import ConfigManager
from archdots.utils import default_editor

CONFIG_PATH = Path(CONFIG_FOLDER) / "config.yaml"

ConfigManager().load()

default_editor(CONFIG_PATH)


