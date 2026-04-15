from rich.syntax import Syntax
from rich.console import Console

from archdots.config.manager import ConfigManager
import yaml

console = Console()
syntax = Syntax(yaml.dump(ConfigManager().load()), "yaml", background_color="default")

console.print(syntax)


