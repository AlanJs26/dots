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
    """
    auxiliary function. call a callback for each key/value inside dict and merge the result
    """
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


def iter_imports(imports_any: Any, recursive=False):
    """
    Returns an Generator for all imported files inside a given config
    """
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

        if recursive:
            with open(import_path, "r") as f:
                imported_config = yaml.safe_load(f)
                if "import" in imported_config:
                    yield from (Path(p) for p in imported_config["import"])

        yield import_path


def compare_mtime_with_imports(config: dict[str, Any], mtime: float) -> bool:
    """
    returns `True` if there is a config file that modification time is more recent than `mtime`
    """
    config_path = Path(CONFIG_FOLDER) / "config.yaml"
    if "import" not in config:
        if config_path.lstat().st_mtime > mtime:
            return True

        return False

    pending = [*iter_imports(config["import"]), config_path]

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


def read_config(use_memo=True) -> dict[Any, Any]:
    """
    read the config file with imports
    `use_memo`: If True, the last processed config will be used. There is also an cache config file that will be used if available.
    """
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
    elif use_memo and _config_memo and config_path.lstat().st_mtime == _last_mtime:
        return _config_memo

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    if CONFIG_CACHE.is_file() and (
        use_memo
        and not compare_mtime_with_imports(config, CONFIG_CACHE.lstat().st_mtime)
    ):
        with open(CONFIG_CACHE, "r") as f:
            cached_config = yaml.safe_load(f)
            if not isinstance(cached_config, dict):
                from rich.console import Console

                warning_console = Console(style="yellow italic", stderr=True)
                warning_console.print("warning: invalid cached config.")
            else:
                return cached_config

    config = iterdict_merge(config, handle_imports)

    with open(module_path / "config.default.yaml", "r") as f:
        default_config = yaml.safe_load(f)

    _config_memo = {**default_config, **config}
    _last_mtime = config_path.lstat().st_mtime

    with open(CONFIG_CACHE, "w") as f:
        yaml.safe_dump(_config_memo, f)

    return _config_memo


def freeze(d: Any):
    """
    Converts any of common types into a hashble data structure
    dict and list -> frozenset
    """
    if isinstance(d, dict):
        fs = frozenset((key, freeze(value)) for key, value in d.items())
        return fs
    elif isinstance(d, list):
        return frozenset(freeze(value) for value in d)
    return d


def unfreeze(d: frozenset):
    """
    Converts a fronzeset into a dict or list
    """
    if not isinstance(d, frozenset):
        return d

    if isinstance(next(iter(d), None), tuple):
        return dict((k, unfreeze(v)) for k, v in d)

    return list(unfreeze(v) for v in d)


def iterdict_imports(
    config: dict[Any, Any],
    merged_config: dict[Any, Any],
    new_merged_config: dict[Any, Any],
    config_path=Path(CONFIG_FOLDER) / "config.yaml",
) -> dict[Any, Any]:
    """
    Traverse a config imports and write changes on correct files
    """

    all_configs = [config]
    all_config_paths = [config_path]
    if "import" in config:
        from itertools import chain

        all_config_paths = list(
            sorted(
                chain(all_config_paths, iter_imports(config["import"])),
                key=lambda p: p.lstat().st_mtime,
                reverse=True,
            )
        )
        all_configs = list(
            map(
                lambda p: yaml.safe_load(p.read_text()),
                all_config_paths,
            )
        )

    for k, v in new_merged_config.items():
        if k in merged_config:
            continue
        config[k] = v

    for current_config, current_config_path in zip(all_configs, all_config_paths):
        if not isinstance(current_config, dict):
            raise SettingsException(
                f'Invalid import. Contents of "{current_config_path}" is not a valid imported config. All imported files must contain at least one field'
            )

        for k, v in current_config.copy().items():
            if k == "import":
                continue
            elif k not in new_merged_config:
                del current_config[k]
            elif isinstance(v, dict):
                if not isinstance(new_merged_config[k], dict):
                    current_config[k] = new_merged_config[k]
                    continue
                if k not in merged_config:
                    continue
                current_config[k] = iterdict_imports(
                    v,
                    merged_config[k],
                    new_merged_config[k],
                    current_config_path,
                )
            elif isinstance(v, list):
                if not isinstance(new_merged_config[k], list):
                    current_config[k] = new_merged_config[k]
                    continue

                new_merged_items = freeze(new_merged_config[k])

                keeped_items = frozenset(freeze(v)).intersection(new_merged_items)

                if k in merged_config:
                    new_items = new_merged_items.difference(freeze(merged_config[k]))
                else:
                    new_items = new_merged_items

                current_config[k] = [*unfreeze(keeped_items), *unfreeze(new_items)]

                new_merged_config[k] = unfreeze(
                    new_merged_items - keeped_items - new_items
                )
            else:
                current_config[k] = new_merged_config[k]

        with open(current_config_path, "w") as f:
            yaml.dump(current_config, f)

    return config


def save_config(data: Any):
    """
    Save a modified config on default location
    """

    merged_config = read_config(False)

    with open(Path(CONFIG_FOLDER) / "config.yaml", "r") as f:
        config = yaml.safe_load(f)
    new_config = iterdict_imports(config, merged_config, data)

    with open(Path(CONFIG_FOLDER) / "config.yaml", "w") as f:
        f.write(yaml.dump(new_config))
