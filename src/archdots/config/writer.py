"""Config file I/O and persistence."""

import yaml
from pathlib import Path
from typing import Any

from archdots.core.constants import CONFIG_FOLDER, MODULE_PATH
from archdots.config.loader import read_config_file
from archdots.config.merger import iterdict_imports


def save_config(data: Any) -> None:
    """Save modified config to disk.

    Distributes changes back to the correct config files
    (considering imports and structure).

    Args:
        data: New configuration data to save
    """
    if not data:
        return

    from archdots.config.manager import ConfigManager

    config_path = Path(CONFIG_FOLDER) / "config.yaml"
    merged_config = ConfigManager().load(use_cache=False)

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    new_config = iterdict_imports(config, merged_config, data)

    with open(config_path, "w") as f:
        f.write(yaml.dump(new_config))
