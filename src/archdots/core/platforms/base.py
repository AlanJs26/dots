from abc import ABC, abstractmethod

class Platform(ABC):
    name: str = ""
    base: str = ""

    @abstractmethod
    def is_current(self) -> bool:
        pass

    def supports(self, platform_name: str) -> bool:
        if platform_name == self.name:
            return True
        if self.base:
            from archdots.core.platforms.registry import get_platform_by_name
            base_platform = get_platform_by_name(self.base)
            if base_platform:
                return base_platform.supports(platform_name)
            return platform_name == self.base
        return False
