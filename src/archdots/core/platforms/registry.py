from archdots.core.platforms.base import Platform

_platforms: list[Platform] = []
_current_platform: Platform | None = None

def get_all_platforms() -> list[Platform]:
    global _platforms
    if not _platforms:
        from archdots.core.platforms.windows import Windows
        from archdots.core.platforms.linux import Linux
        from archdots.core.platforms.archlinux import ArchLinux
        from archdots.core.platforms.ubuntu import Ubuntu
        from archdots.core.platforms.debian import Debian
        from archdots.core.platforms.fedora import Fedora
        from archdots.core.platforms.hyprland import Hyprland
        from archdots.core.platforms.bspwm import Bspwm

        # Check most specific first to avoid matching generic Linux/Windows early
        _platforms = [
            Hyprland(),
            Bspwm(),
            ArchLinux(),
            Ubuntu(),
            Debian(),
            Fedora(),
            Linux(),
            Windows(),
        ]
    return _platforms

def get_platform_by_name(name: str) -> Platform | None:
    for p in get_all_platforms():
        if p.name == name:
            return p
    return None

def get_current_platform() -> Platform:
    global _current_platform
    if _current_platform is None:
        for p in get_all_platforms():
            if p.is_current():
                _current_platform = p
                break
        if _current_platform is None:
            import os
            from archdots.core.platforms.windows import Windows
            from archdots.core.platforms.linux import Linux
            _current_platform = Windows() if os.name == "nt" else Linux()
    return _current_platform
