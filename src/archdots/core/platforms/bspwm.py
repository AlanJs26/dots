import os
import subprocess
from archdots.core.platforms.base import Platform


class Bspwm(Platform):
    name = "bspwm"
    base = ["ubuntu", "archlinux"]

    def is_current(self) -> bool:
        if os.name != "posix":
            return False

        try:
            return (
                subprocess.run(
                    ["pgrep", "-x", "bspwm"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                ).returncode
                == 0
            )
        except FileNotFoundError, Exception:
            return False
