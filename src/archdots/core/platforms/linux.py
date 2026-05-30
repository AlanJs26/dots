import os
from archdots.core.platforms.base import Platform

class Linux(Platform):
    name = "linux"
    base = ""

    def is_current(self) -> bool:
        return os.name == "posix"
