import os
import subprocess
from archdots.core.platforms.base import Platform

class Hyprland(Platform):
    name = "hyprland"
    base = "linux"

    def is_current(self) -> bool:
        if os.name != "posix":
            return False
        
        # Hyprland sets this env var
        if "HYPRLAND_INSTANCE_SIGNATURE" in os.environ:
            return True
            
        # Fallback to pgrep
        try:
            return subprocess.run(["pgrep", "-x", "Hyprland"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
        except (FileNotFoundError, Exception):
            return False
