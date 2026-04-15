import json
import os
from pathlib import Path

from dacite.core import from_dict

from archdots.schema import Metadata, ExtendedJSONEncoder


def load_cached_metadata(
    cache_folder: str, command_tree_json: str
) -> dict[str, Metadata] | None:
    cached_command_tree_path = Path(cache_folder) / "command_tree.json"
    cached_metadata_dict_path = Path(cache_folder) / "metadata_dict.json"

    if not (cached_command_tree_path.is_file() and cached_metadata_dict_path.is_file()):
        return None

    with open(cached_command_tree_path, "r") as f:
        cached_command_tree = f.read()

    try:
        if command_tree_json != cached_command_tree:
            return None

        with open(cached_metadata_dict_path, "r") as f:
            raw_metadata = json.load(f)

        return {key: from_dict(Metadata, value) for key, value in raw_metadata.items()}
    except Exception:
        return None


def save_parser_cache(cache_folder: str, command_tree_json: str, metadata_dict) -> None:
    os.makedirs(cache_folder, exist_ok=True)

    cached_command_tree_path = Path(cache_folder) / "command_tree.json"
    cached_metadata_dict_path = Path(cache_folder) / "metadata_dict.json"

    with open(cached_command_tree_path, "w") as f:
        f.write(command_tree_json)

    with open(cached_metadata_dict_path, "w") as f:
        json.dump(metadata_dict, f, cls=ExtendedJSONEncoder)
