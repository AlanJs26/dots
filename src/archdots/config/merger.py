"""Config file merging and transformation utilities."""

from collections.abc import Callable, Mapping, MutableMapping, MutableSequence
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

    # We use a copy to avoid mutating the original during traversal
    # but we must be careful with CommentedMap if we want to preserve it.
    # However, iterdict_merge is mostly used for loading, where we merge
    # imports into a final result.
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
        
        # Remove keys not in source (if target is meant to be a full sync)
        # Note: In our config system, we usually only sync keys that are present.
        # However, for full sync, we might need to delete.
        for key in list(target.keys()):
            if key not in source:
                del target[key]
                
    elif isinstance(target, MutableSequence) and isinstance(source, list):
        # For sequences, a full replacement is often safer for comments 
        # unless we want to try element matching.
        # But ruamel sequences also have comments.
        target[:] = source


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
                    # For complex structures, we check if they were in the previous merged state
                    if k in merged_config:
                        # Recursively update
                        if isinstance(v, dict) and isinstance(new_v, dict):
                            update_in_place(v, new_v)
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

