import subprocess

from archdots.ui.console import err_console
from archdots.ui.progress import progress_decorator
from archdots.packages.managers.base import PackageManager
from archdots.packages.managers.custom import Custom
from archdots.utils.decorators import memoize


class Scoop(PackageManager):
    def __init__(self) -> None:
        super().__init__("scoop")

    @progress_decorator("scoop packages")
    @memoize
    def get_installed(self, use_memo=False, by_user=True) -> list[str]:
        import json

        try:
            process = subprocess.run(
                'powershell -Command "(scoop list 6> $null)|ConvertTo-Json"',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                text=True,
                encoding="utf-8",
                timeout=30,
            )

            if process.returncode != 0 or not process.stdout.strip():
                return []

            scoop_result = json.loads(process.stdout)
            pkg_names = [result["Name"] for result in scoop_result]
            custom_package_names = [pkg.name for pkg in Custom().get_packages(use_memo=use_memo)]
            return list(filter(lambda p: p not in custom_package_names, pkg_names))
        except json.JSONDecodeError:
            return []
        except subprocess.TimeoutExpired:
            err_console.print("[warning]scoop list command timed out[/warning]")
            return []
        except Exception as e:
            err_console.print(f"[warning]error running scoop list: {e}[/warning]")
            return []

    def install(self, packages: list[str], force=True) -> bool:
        if not packages:
            return True
        from os import system

        error_happened = False
        for package in packages:
            error_happened = error_happened or system(f'scoop install "{package}"') != 0
        return not error_happened

    def uninstall(self, packages: list[str]) -> bool:
        if not packages:
            return True
        from os import system

        error_happened = False
        for package in packages:
            error_happened = error_happened or system(f'scoop uninstall "{package}"') != 0
        return not error_happened

    def is_available(self) -> bool:
        from shutil import which

        return which("scoop") is not None
