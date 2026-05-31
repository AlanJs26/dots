"""Config loading and import resolution."""

import os
import yaml
from pathlib import Path
from typing import Any, Generator

from archdots.core.constants import CONFIG_FOLDER, MODULE_PATH
from archdots.core.exceptions import SettingsException
from archdots.ui.console import warn_console
from archdots.config.yaml_instance import yaml_rt


def iter_imports(imports_any: Any, recursive: bool = False) -> Generator[Path, None, None]:
    """Resolve and yield all imported config files.

    Args:
        imports_any: String path, list of paths, or import specification
        recursive: If True, also yield nested imports recursively

    Yields:
        Path objects for all imported config files

    Raises:
        SettingsException: If import specification is invalid
    """
    custom_folder = Path(CONFIG_FOLDER)

    from archdots.core.platforms.registry import get_current_platform
    current_platform = get_current_platform()

    if isinstance(imports_any, str):
        raw_imports: list[Any] = [imports_any]
    elif isinstance(imports_any, list):
        raw_imports = imports_any
    else:
        raise SettingsException(
            "Invalid import. Expecting a path and found an object instead"
        )

    for item in raw_imports:
        if isinstance(item, str):
            imp = item
        elif isinstance(item, dict):
            if len(item) != 1:
                raise SettingsException(f"Invalid import specification: {item}")
            imp, platform_req = list(item.items())[0]
            if not current_platform.supports(platform_req):
                continue
        else:
            raise SettingsException(
                f"Invalid import. Expecting a path (str) or a platform-specific path (dict), found {type(item).__name__}"
            )

        if imp.startswith("."):
            import_path = (custom_folder / imp).resolve()
        else:
            import_path = Path(imp).resolve()

        if not os.path.isfile(import_path):
            raise SettingsException(f'Invalid import. "{import_path}" is not a file')

        yield import_path

        if recursive:
            with open(import_path, "r") as f:
                # Use PyYAML for fast check
                imported_config = yaml.safe_load(f)
                if isinstance(imported_config, dict) and "import" in imported_config:
                    yield from iter_imports(imported_config["import"], recursive=True)


def compare_mtime_with_imports(config: dict[str, Any], mtime: float) -> bool:
    """Check if any config file is newer than the given mtime.

    Args:
        config: Configuration dictionary (may contain 'import' key)
        mtime: Modification time threshold

    Returns:
        True if any config file is newer than mtime, False otherwise

    Raises:
        SettingsException: If config file is invalid
    """
    config_path = Path(CONFIG_FOLDER) / "config.yaml"
    
    # Check main config file
    if config_path.exists() and config_path.lstat().st_mtime > mtime:
        return True

    if "import" not in config:
        return False

    for imp_path in iter_imports(config["import"], recursive=True):
        if imp_path.lstat().st_mtime > mtime:
            return True

    return False


def read_config_file(config_path: Path) -> dict[str, Any]:
    """Load and parse a single config YAML file using PyYAML for speed.

    Args:
        config_path: Path to config file

    Returns:
        Parsed configuration dict
    """
    module_path = Path(MODULE_PATH)
    custom_folder = Path(CONFIG_FOLDER)

    # Create default config if missing
    if not os.path.isfile(config_path):
        os.makedirs(custom_folder, exist_ok=True)
        with open(module_path / "chezmoi_template/archdots/config.yaml", "r") as f:
            default_config = f.read()
        with open(config_path, "w") as f:
            f.write(default_config)

    with open(config_path, "r") as f:
        # Use PyYAML for fast loading of the raw config
        config = yaml.safe_load(f)
    
    return config if isinstance(config, dict) else {}
