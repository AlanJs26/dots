from abc import ABC, abstractmethod


class Platform(ABC):
    name: str = ""
    base: list[str] = []

    @abstractmethod
    def is_current(self) -> bool:
        pass

    def supports(self, platform_name: str) -> bool:
        if platform_name == self.name:
            return True
        if len(self.base):
            from archdots.core.platforms.registry import get_platform_by_name

            for base in self.base:
                base_platform = get_platform_by_name(base)
                if base_platform:
                    return base_platform.supports(platform_name)
            return platform_name in self.base
        return False
