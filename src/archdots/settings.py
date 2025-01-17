from collections.abc import Callable
import os
from pathlib import Path
import yaml
from typing import Any

from archdots.constants import CACHE_FOLDER, CONFIG_FOLDER, MODULE_PATH
from archdots.exceptions import SettingsException

CONFIG_CACHE = Path(CACHE_FOLDER) / "config.yaml.cache"

_config_memo: dict[Any, Any] = {}
_last_mtime = 0


def iterdict_merge(
    d: dict[Any, Any], callback: Callable[[Any, Any], Any]
) -> dict[Any, Any]:
    from deepmerge import always_merger

    d_copy = d.copy()
    for k, v in d.items():
        if isinstance(v, dict):
            d_copy[k] = iterdict_merge(v, callback)
        elif (result := callback(k, v)) != None:
            always_merger.merge(d_copy, iterdict_merge(result, callback))
            # d_copy = {**d, **iterdict_merge(result, callback)}
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


def compare_mtime_with_imports(config: dict[str, Any], mtime: float):
    if "import" not in config:
        return False

    pending = [*iter_imports(config["import"])]

    while pending:
        next_import = pending.pop()

        if next_import.lstat().st_mtime > mtime:
            return True

        if not next_import.is_file():
            raise SettingsException("invalid config file")
        with open(next_import, "r") as f:
            next_config = yaml.safe_load(f)

        if "import" in next_config:
            if isinstance(next_config["import"], str):
                pending.append(next_config["import"])
            else:
                pending.extend(next_config["import"])

    return False


def read_config(use_memo=False):
    global _last_mtime
    global _config_memo
    module_path = Path(MODULE_PATH)
    custom_folder = Path(CONFIG_FOLDER)
    config_path = custom_folder / "config.yaml"

    def handle_imports(key: Any, value: Any):
        if key != "import":
            return

        from deepmerge import always_merger

        merged_value = {}
        for import_path in iter_imports(value):
            with open(import_path, "r") as f:
                imported_config = yaml.safe_load(f)
                if not isinstance(imported_config, dict):
                    raise SettingsException(
                        f'Invalid import. Contents of "{import_path}" is not a valid imported config. All imported files must contain at least one field'
                    )
            always_merger.merge(merged_value, imported_config)
            # merged_value = {**merged_value, **imported_config}

        return merged_value

    if not os.path.isfile(config_path):
        os.makedirs(custom_folder)
        with open(module_path / "config.default.yaml", "r") as f:
            default_config = f.read()
        with open(config_path, "w") as f:
            f.write(default_config)
    elif _config_memo and config_path.lstat().st_mtime == _last_mtime:
        return _config_memo

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    if CONFIG_CACHE.is_file() and (
        use_memo or compare_mtime_with_imports(config, config_path.lstat().st_mtime)
    ):
        with open(CONFIG_CACHE, "r") as f:
            return yaml.safe_load(f)

    config = iterdict_merge(config, handle_imports)

    with open(module_path / "config.default.yaml", "r") as f:
        default_config = yaml.safe_load(f)

    _config_memo = {**default_config, **config}
    _last_mtime = config_path.lstat().st_mtime

    with open(CONFIG_CACHE, "w") as f:
        yaml.safe_dump(_config_memo, f)

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

    # :TODO: handle merging lists across imported files
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
                with open(import_path, "w") as f:
                    f.write(
                        yaml.dump(
                            iterdict_imports(
                                config, imported_config, d, ignore_new=True
                            )
                        )
                    )
        else:
            d_copy[k] = d[k]
    return d_copy


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

    with open(custom_folder / "config.yaml", "w") as f:
        f.write(yaml.dump(new_config))
