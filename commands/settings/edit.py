from archdots.constants import CONFIG_FOLDER
from pathlib import Path

import os

from archdots.settings import read_config

CONFIG_PATH = Path(CONFIG_FOLDER) / "config.yaml"

read_config()

os.system(f'$EDITOR "{CONFIG_PATH}"')
