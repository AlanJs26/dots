from collections.abc import Callable
import os
from pathlib import Path
import yaml
from typing import Any
from src.constants import CONFIG_FOLDER, MODULE_PATH


def iterdict(d: dict[Any, Any], callback: Callable[[Any, Any], Any]) -> dict[Any, Any]:
    d_copy = d.copy()
    for k, v in d.items():
        if isinstance(v, dict):
            d_copy[k] = iterdict(v, callback)
        elif (result := callback(k, v)) != None:
            d_copy = {**d, **result}
            del d_copy[k]
    return d_copy


def read_config(custom_folder=CONFIG_FOLDER):
    module_path = Path(MODULE_PATH)

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
        config = iterdict(config, handle_imports)

    with open(module_path / "config.default.yaml", "r") as f:
        default_config = yaml.safe_load(f)

    return {**default_config, **config}


def save_config(data: Any, custom_folder=CONFIG_FOLDER):
    custom_folder = Path(os.path.expanduser(custom_folder))

    with open(custom_folder / "config.yaml", "w") as f:
        yaml.dump(data, f)
