"""Config loading and import resolution."""

import os
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
                imported_config = yaml_rt.load(f)
                if "import" in imported_config:
                    yield from (Path(p) for p in imported_config["import"])

        yield import_path


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
            next_config = yaml_rt.load(f)

        if "import" in next_config:
            if isinstance(next_config["import"], str):
                pending.append(Path(CONFIG_FOLDER) / next_config["import"])
            else:
                pending.extend((Path(CONFIG_FOLDER) / p) for p in next_config["import"])

    return False


def read_config_file(config_path: Path) -> dict[str, Any]:
    """Load and parse a single config YAML file.

    Args:
        config_path: Path to config file

    Returns:
        Parsed configuration dict

    Raises:
        SettingsException: If file is not found or invalid
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
        config = yaml_rt.load(f)
    
    return config if isinstance(config, (dict, Any)) else {}

