from src.constants import CONFIG_FOLDER
from pathlib import Path
from rich.syntax import Syntax
from rich.console import Console

import os

from src.settings import read_config
import yaml

CONFIG_PATH = Path(CONFIG_FOLDER) / "config.yaml"

console = Console()
syntax = Syntax(yaml.dump(read_config()), "yaml", background_color="default")

console.print(syntax)
