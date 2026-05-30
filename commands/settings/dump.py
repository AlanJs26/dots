from rich.syntax import Syntax
from rich.console import Console
from io import StringIO

from archdots.config.manager import ConfigManager
from archdots.config.yaml_instance import yaml_rt

console = Console()

# Use yaml_rt to dump the config to a string to preserve clean formatting
stream = StringIO()
yaml_rt.dump(ConfigManager().load(), stream)
yaml_text = stream.getvalue()

syntax = Syntax(yaml_text, "yaml", background_color="default")
console.print(syntax)


