from collections.abc import Callable
import os
from pathlib import Path
import yaml
from typing import Any, Iterable
from src.constants import CONFIG_FOLDER, MODULE_PATH
from rich import print

_config_memo: dict[Any, Any] = {}
_last_mtime = 0


class SettingsException(Exception):
    pass


def iterdict_merge(
    d: dict[Any, Any], callback: Callable[[Any, Any], Any]
) -> dict[Any, Any]:
    d_copy = d.copy()
    for k, v in d.items():
        if isinstance(v, dict):
            d_copy[k] = iterdict_merge(v, callback)
        elif (result := callback(k, v)) != None:
            d_copy = {**d, **iterdict_merge(result, callback)}
            del d_copy[k]
    return d_copy


def iter_imports(imports_any: Any):
    custom_folder = Path(CONFIG_FOLDER)

    if isinstance(imports_any, str):
        imports: list[str] = [imports_any]
    elif isinstance(imports_any, list):
        if not all(isinstance(x, str) for x in imports_any):
            raise SettingsException(
                "Invalid import. Expecting a list of paths and found an object instead"
            )
        imports: list[str] = imports_any
    else:
        raise SettingsException(
            "Invalid import. Expecting a path and found an object instead"
        )

    for imp in imports:
        if imp.startswith("."):
            import_path = (custom_folder / imp).resolve()
        else:
            import_path = Path(imp).resolve()

        if not os.path.isfile(import_path):
            raise SettingsException(f'Invalid import. "{import_path}" is not a file')

        yield import_path


def read_config():
    global _last_mtime
    global _config_memo
    module_path = Path(MODULE_PATH)
    custom_folder = Path(CONFIG_FOLDER)
    config_path = custom_folder / "config.yaml"

    if not os.path.isfile(config_path):
        os.makedirs(custom_folder)
        with open(module_path / "config.default.yaml", "r") as f:
            default_config = f.read()
        with open(config_path, "w") as f:
            f.write(default_config)
    elif _config_memo and config_path.lstat().st_mtime == _last_mtime:
        return _config_memo

    def handle_imports(key: Any, value: Any):
        if key != "import":
            return

        merged_value = {}
        for import_path in iter_imports(value):
            with open(import_path, "r") as f:
                imported_config = yaml.safe_load(f)
                if not isinstance(imported_config, dict):
                    raise SettingsException(
                        f'Invalid import. Contents of "{import_path}" is not a valid imported config. All imported files must contain at least one field'
                    )
            merged_value = {**merged_value, **imported_config}

        return merged_value

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
        config = iterdict_merge(config, handle_imports)

    with open(module_path / "config.default.yaml", "r") as f:
        default_config = yaml.safe_load(f)

    _config_memo = {**default_config, **config}
    _last_mtime = config_path.lstat().st_mtime
    return _config_memo


def iterdict_imports(
    config: dict[Any, Any],
    d_original: dict[Any, Any],
    d: dict[Any, Any],
    ignore_new=False,
) -> dict[Any, Any]:
    d_copy = d_original.copy()
    if not ignore_new:
        for k, v in d.items():
            if k in config:
                continue
            d_copy[k] = v

    for k, v in d_original.items():
        if k not in d and k != "import":
            del d_copy[k]
        elif isinstance(v, dict):
            d_copy[k] = iterdict_imports(config[k], d_original[k], d[k])
        elif k == "import":
            for import_path in iter_imports(v):
                with open(import_path, "r") as f:
                    imported_config = yaml.safe_load(f)
                    if not isinstance(imported_config, dict):
                        raise SettingsException(
                            f'Invalid import. Contents of "{import_path}" is not a valid imported config. All imported files must contain at least one field'
                        )
                    print(f"\n=== {import_path}")
                    print(iterdict_imports(config, imported_config, d, ignore_new=True))
                # with open(import_path, 'w') as f:
                #     f.write(
                #         yaml.dump(iterdict_imports(config, d_copy, imported_config))
                #     )
        else:
            d_copy[k] = d[k]
    return d_copy


"""
# conteudo de config.yaml
import: ./bla
coisa: 1
so_original: 1

# conteudo de bla
item_bla: 1

# conteudo de novo_config.yaml
item_bla: novo
coisa: 2
novo_item: 1

"""


def save_config(data: Any):
    module_path = Path(MODULE_PATH)
    custom_folder = Path(CONFIG_FOLDER)

    if not os.path.isfile(custom_folder / "config.yaml"):
        os.makedirs(custom_folder)
        with open(module_path / "config.default.yaml", "r") as f:
            default_config = f.read()
        with open(custom_folder / "config.yaml", "w") as f:
            f.write(default_config)

    merged_config = read_config()
    with open(custom_folder / "config.yaml", "r") as f:
        config = yaml.safe_load(f)
        new_config = iterdict_imports(merged_config, config, data)  # type: ignore
    print(f"\n=== config.yaml")
    print(new_config)
