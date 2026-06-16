import os
from archdots.core.platforms.base import Platform


class Ubuntu(Platform):
    name = "ubuntu"
    base = ["debian"]

    def is_current(self) -> bool:
        if os.path.exists("/etc/os-release"):
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("ID=") and "ubuntu" in line.strip().lower():
                        return True
        return False
