"""Config file merging and transformation utilities."""

from collections.abc import Callable
from typing import Any


def iterdict_merge(
    d: dict[Any, Any], callback: Callable[[Any, Any], Any]
) -> dict[Any, Any]:
    """Recursively merge dictionary with callback results.

    Traverses a dict, calling callback for each key/value. If callback returns
    a value, that value is merged into the result dict at that key.

    Args:
        d: Dictionary to process
        callback: Function taking (key, value) and returning dict or None

    Returns:
        Merged dictionary
    """
    from deepmerge import always_merger

    d_copy = d.copy()
    for k, v in d.items():
        if isinstance(v, dict):
            d_copy[k] = iterdict_merge(v, callback)
        elif (result := callback(k, v)) is not None:
            always_merger.merge(d_copy, iterdict_merge(result, callback))
            del d_copy[k]
    return d_copy


def freeze(d: Any) -> frozenset:
    """Convert dict/list to hashable frozenset structure.

    Recursively converts:
    - dict -> frozenset of (key, freeze(value)) tuples
    - list -> frozenset of freeze(item) items
    - other -> unchanged

    Args:
        d: Data structure to freeze

    Returns:
        Hashable frozenset representation
    """
    if isinstance(d, dict):
        fs = frozenset((key, freeze(value)) for key, value in d.items())
        return fs
    elif isinstance(d, list):
        return frozenset(freeze(value) for value in d)
    return d


def unfreeze(d: frozenset) -> Any:
    """Convert frozenset back to dict/list structure.

    Inverse of freeze(): converts frozenset representations back to dicts/lists.

    Args:
        d: Frozenset (or other data) to unfreeze

    Returns:
        Unfrozen dict/list/other structure
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
    config_path,
) -> dict[Any, Any]:
    """Traverse config imports and write changes to correct files.

    Distributes changes from new_merged_config back into the original
    config files (considering imports and file modification times).

    Args:
        config: Current config dict
        merged_config: Previously merged config (for diff)
        new_merged_config: New config values to apply
        config_path: Path to main config file

    Returns:
        Updated config dict

    Raises:
        SettingsException: If config structure is invalid
    """
    from pathlib import Path
    import yaml
    from itertools import chain
    from archdots.core.exceptions import SettingsException
    from archdots.config.loader import iter_imports

    all_configs = [config]
    all_config_paths = [config_path]
    if "import" in config:
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
                f'Invalid import. Contents of "{current_config_path}" is not a valid config'
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
