from archdots.constants import CONFIG_FOLDER
from pathlib import Path

from archdots.settings import read_config
from archdots.utils import default_editor

CONFIG_PATH = Path(CONFIG_FOLDER) / "config.yaml"

read_config()

default_editor(CONFIG_PATH)
