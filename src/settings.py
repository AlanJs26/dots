from collections.abc import Callable
import os
from pathlib import Path
import yaml
from typing import Any


def iterdict(d, callback: Callable[[Any, Any], Any]):
    for k, v in d.items():
        if isinstance(v, dict):
            iterdict(v, callback)
        elif (result := callback(k, v)) != None:
            d[k] = result


def read_config(custom_folder="~/.config/archdots"):
    import src

    module_path = Path(list(src.__path__)[0]).parent

    custom_folder = Path(os.path.expanduser(custom_folder))

    if not os.path.isfile(custom_folder / "config.yaml"):
        os.makedirs(custom_folder)
        with open(module_path / "config.default.yaml", "r") as f:
            default_config = f.read()
        with open(custom_folder / "config.yaml", "w") as f:
            f.write(default_config)

    def handle_imports(key: Any, value: Any):
        if key != "import" or not isinstance(value, str):
            return

        if value.startswith("."):
            import_path = (custom_folder / value).resolve()
        else:
            import_path = Path(value).resolve()

        if not os.path.isfile(import_path):
            return

        # print(import_path)
        with open(import_path, "r") as f:
            return yaml.safe_load(f)

    with open(custom_folder / "config.yaml", "r") as f:
        config = yaml.safe_load(f)
        iterdict(config, handle_imports)

    return config
