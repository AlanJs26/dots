from rich.syntax import Syntax
from rich.console import Console

from archdots.settings import read_config
import yaml

console = Console()
syntax = Syntax(yaml.dump(read_config()), "yaml", background_color="default")

console.print(syntax)
