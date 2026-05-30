"""Core constants: paths, platform, module locations."""

from importlib.metadata import Distribution, PackageNotFoundError
from importlib import resources
from pathlib import Path
import archdots
import shutil
import json
import os

def is_editable_install(package_name: str) -> bool:
    """Retorna True se o pacote especificado estiver instalado em modo editável (-e)."""
    try:
        # Carrega os metadados oficiais de instalação do pacote
        dist = Distribution.from_name(package_name)
        direct_url_text = dist.read_text("direct_url.json")
        
        if direct_url_text:
            data = json.loads(direct_url_text)
            # Verifica a marcação 'editable' conforme a especificação do Python (PEP 660)
            return data.get("dir_info", {}).get("editable", False)
            
    except (PackageNotFoundError, json.JSONDecodeError, KeyError):
        # Se o pacote não foi instalado ainda (rodando solto) ou deu erro
        pass
        
    return False

# Platform detection
from archdots.core.platforms.registry import get_current_platform
_current_platform = get_current_platform()
PLATFORM = _current_platform.name

if _current_platform.supports("windows"):
    CACHE_FOLDER = os.path.expanduser("~/AppData/Local/Temp/archdots")
else:
    CACHE_FOLDER = os.path.expanduser("~/.cache/archdots")

# Standard folders
CONFIG_FOLDER = os.path.expanduser("~/.config/archdots")
CHEZMOI_FOLDER = os.path.expanduser("~/.local/share/chezmoi")

# Config subfolders
COMMANDS_FOLDER = os.path.join(CONFIG_FOLDER, "commands")
HEALTH_FOLDER = os.path.join(CONFIG_FOLDER, "health")
PACKAGES_FOLDER = os.path.join(CONFIG_FOLDER, "packages")

# Module location
if is_editable_install("archdots"):
    MODULE_PATH = str(Path(list(archdots.__path__)[0]).parent.parent)
else:
    share_path = Path.home() / ".local" / "share" / "archdots"
    MODULE_PATH = str(share_path)
    
    if not share_path.is_dir():
        share_path.parent.mkdir(exist_ok=True)

        resource_root = resources.files("archdots")

        resource_list = ["commands", "chezmoi_template", "default_packages"]

        for resource_path in resource_list:
            res = resource_root.joinpath(resource_path)

            with resources.as_file(res) as real_path:
                shutil.copytree(real_path, share_path / resource_path, dirs_exist_ok=True)
