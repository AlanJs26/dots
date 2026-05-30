"""
ARCHDOTS
help: query settings using simple dot notation (e.g. .field1.subfield)
arguments:
  - name: query
    required: true
    type: str
    nargs: 1
    help: query string (e.g. .apps.terminal)
flags:
  - long: --raw
    type: bool
    help: output raw value instead of pretty-printed YAML
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

from archdots.config.manager import ConfigManager
from archdots.config.yaml_instance import yaml_rt
from rich.console import Console
from rich.syntax import Syntax
from io import StringIO
import sys

console = Console()

def resolve_query(data, query):
    if not query or query == ".":
        return data
    
    # Remove leading dot
    if query.startswith("."):
        query = query[1:]
    
    parts = query.split(".")
    current = data
    for part in parts:
        if not part: continue
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif isinstance(current, list):
            try:
                index = int(part)
                current = current[index]
            except (ValueError, IndexError):
                print(f"Error: Invalid index or property '{part}'", file=sys.stderr)
                return None
        else:
            print(f"Error: Property '{part}' not found", file=sys.stderr)
            return None
    return current

config = ConfigManager().load()
query_arg = args["query"]
if isinstance(query_arg, list):
    query_arg = " ".join(query_arg)

result = resolve_query(config, query_arg)

if result is not None:
    if args["raw"] and not isinstance(result, (dict, list)):
        print(result)
    else:
        stream = StringIO()
        yaml_rt.dump(result, stream)
        yaml_text = stream.getvalue().strip()
        
        syntax = Syntax(yaml_text, "yaml", background_color="default")
        console.print(syntax)


