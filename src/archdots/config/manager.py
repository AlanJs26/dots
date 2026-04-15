"""Configuration manager facade.

Consolidates:
- File loading (with import resolution)
- Caching (in-memory and disk)
- Merging (combining defaults with user config)
- Saving (writing back to disk)
"""

import os
import yaml
from pathlib import Path
from typing import Any

from archdots.core.constants import CACHE_FOLDER, CONFIG_FOLDER, MODULE_PATH
from archdots.core.exceptions import SettingsException
from archdots.utils.decorators import SingletonMeta
from archdots.ui.console import warn_console
from archdots.config.loader import (
    read_config_file,
    iter_imports,
    compare_mtime_with_imports,
)
from archdots.config.merger import iterdict_merge, iterdict_imports


class ConfigManager(metaclass=SingletonMeta):
    """Unified configuration manager with caching and import support."""

    def __init__(self):
        """Initialize config manager."""
        self._config_memo: dict[Any, Any] = {}
        self._last_mtime: float = 0
        self._cache_path = Path(CACHE_FOLDER) / "config.yaml.cache"

    def load(self, use_cache: bool = True) -> dict[Any, Any]:
        """Load config with optional caching.

        Resolves imports, merges with defaults, and optionally uses cached version.

        Args:
            use_cache: If True, use in-memory cache and disk cache when available

        Returns:
            Complete configuration dictionary
        """
        config_path = Path(CONFIG_FOLDER) / "config.yaml"

        # Check in-memory cache
        if (
            use_cache
            and self._config_memo
            and config_path.lstat().st_mtime == self._last_mtime
        ):
            return self._config_memo

        config = read_config_file(config_path)

        # Check disk cache
        if self._cache_path.is_file() and (
            use_cache
            and not compare_mtime_with_imports(config, self._cache_path.lstat().st_mtime)
        ):
            with open(self._cache_path, "r") as f:
                cached_config = yaml.safe_load(f)
                if isinstance(cached_config, dict):
                    return cached_config
                warn_console.print("warning: invalid cached config")

        # Process imports and merge
        def handle_imports(key: Any, value: Any) -> Any:
            if key != "import":
                return None

            from deepmerge import always_merger

            merged_value = {}
            for import_path in iter_imports(value):
                with open(import_path, "r") as f:
                    imported_config = yaml.safe_load(f)
                    if not isinstance(imported_config, dict):
                        raise SettingsException(
                            f'Invalid import. Contents of "{import_path}" is not a valid config'
                        )
                always_merger.merge(merged_value, imported_config)

            return merged_value

        config = iterdict_merge(config, handle_imports)

        # Merge with defaults
        with open(Path(MODULE_PATH) / "config.default.yaml", "r") as f:
            default_config = yaml.safe_load(f)

        self._config_memo = {**default_config, **config}
        self._last_mtime = config_path.lstat().st_mtime

        # Save to cache
        os.makedirs(CACHE_FOLDER, exist_ok=True)
        with open(self._cache_path, "w") as f:
            yaml.safe_dump(self._config_memo, f)

        return self._config_memo

    def save(self, data: Any) -> None:
        """Save configuration changes to disk.

        Args:
            data: New config data to save
        """
        if not data:
            return

        config_path = Path(CONFIG_FOLDER) / "config.yaml"
        merged_config = self.load(use_cache=False)

        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        new_config = iterdict_imports(config, merged_config, data)

        with open(config_path, "w") as f:
            f.write(yaml.dump(new_config))

        # Invalidate cache after save
        self._config_memo = {}
        self._last_mtime = 0
