import os
from archdots.core.platforms.base import Platform

class Windows(Platform):
    name = "windows"
    base = ""

    def is_current(self) -> bool:
        return os.name == "nt"
