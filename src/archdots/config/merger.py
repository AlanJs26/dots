"""Config file merging and transformation utilities."""

from collections.abc import Callable, Mapping, MutableMapping, MutableSequence
from typing import Any


def merge_unique(base: dict[Any, Any], nxt: dict[Any, Any]) -> dict[Any, Any]:
    """Merge nxt into base, ensuring no duplicate items in lists."""
    for k, v in nxt.items():
        if k in base:
            if isinstance(base[k], dict) and isinstance(v, dict):
                merge_unique(base[k], v)
            elif isinstance(base[k], list) and isinstance(v, list):
                # For lists, we append only new items. 
                # For dicts in lists, we check for equality.
                for item in v:
                    if item not in base[k]:
                        base[k].append(item)
            else:
                base[k] = v
        else:
            base[k] = v
    return base


def iterdict_merge(
    d: dict[Any, Any], callback: Callable[[Any, Any], Any]
) -> dict[Any, Any]:
    """Recursively merge dictionary with callback results, avoiding duplicates."""
    res = {}
    
    # 1. Process regular keys first
    for k, v in d.items():
        if k == "import":
            continue
        if isinstance(v, dict):
            res[k] = iterdict_merge(v, callback)
        else:
            res[k] = v
            
    # 2. Process imports and merge them into the result
    if "import" in d:
        imported_data = callback("import", d["import"])
        if imported_data:
            # Recurse into imported data to handle nested imports
            processed_imported = iterdict_merge(imported_data, callback)
            # Merge into res ensuring uniqueness
            merge_unique(res, processed_imported)
            
    return res


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


def update_in_place(target: Any, source: Any) -> None:
    """Update target object in-place with data from source, preserving types.

    Args:
        target: Object to update (CommentedMap, CommentedSeq, dict, list)
        source: Source data
    """
    if isinstance(target, MutableMapping) and isinstance(source, Mapping):
        # Update keys in mapping
        for key, value in source.items():
            if key in target:
                if isinstance(target[key], (MutableMapping, MutableSequence)) and isinstance(
                    value, (Mapping, list)
                ):
                    update_in_place(target[key], value)
                else:
                    target[key] = value
            else:
                target[key] = value
        
        # Remove keys not in source
        for key in list(target.keys()):
            if key not in source:
                del target[key]
                
    elif isinstance(target, MutableSequence) and isinstance(source, list):
        target[:] = source


def iterdict_imports(
    config: dict[Any, Any],
    merged_config: dict[Any, Any],
    new_merged_config: dict[Any, Any],
    config_path,
) -> dict[Any, Any]:
    """Traverse config imports and write changes to correct files."""
    from pathlib import Path
    from itertools import chain
    from archdots.core.exceptions import SettingsException
    from archdots.config.loader import iter_imports
    from archdots.config.yaml_instance import yaml_rt

    all_configs: list[Any] = [config]
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
                lambda p: yaml_rt.load(p.read_text()),
                all_config_paths,
            )
        )

    # Apply new keys to the root config if they are completely new
    for k, v in new_merged_config.items():
        if k not in merged_config:
            config[k] = v

    updated_main_config = config

    for current_config, current_config_path in zip(all_configs, all_config_paths):
        if not isinstance(current_config, dict):
            raise SettingsException(
                f'Invalid import. Contents of "{current_config_path}" is not a valid config'
            )

        # Mutate current_config in-place
        for k in list(current_config.keys()):
            if k == "import":
                continue
            
            if k not in new_merged_config:
                del current_config[k]
            else:
                v = current_config[k]
                new_v = new_merged_config[k]
                
                if isinstance(v, (dict, list)) and isinstance(new_v, (dict, list)):
                    if k in merged_config:
                        if isinstance(v, dict) and isinstance(new_v, dict):
                            update_in_place(v, new_v)
                        elif isinstance(v, list) and isinstance(new_v, list):
                            new_merged_items = freeze(new_v)
                            keeped_items = frozenset(freeze(v)).intersection(new_merged_items)
                            
                            # Only add TRULY new items to the main config
                            if current_config_path == config_path:
                                new_items = new_merged_items.difference(freeze(merged_config[k]))
                                current_config[k] = [*unfreeze(keeped_items), *unfreeze(new_items)]
                            else:
                                current_config[k] = [*unfreeze(keeped_items)]
                        else:
                            current_config[k] = new_v
                    else:
                        current_config[k] = new_v
                else:
                    current_config[k] = new_v

        if current_config_path == config_path:
            updated_main_config = current_config

        with open(current_config_path, "w") as f:
            yaml_rt.dump(current_config, f)

    return updated_main_config
