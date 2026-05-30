import subprocess
from typing import TypedDict

from archdots.ui.console import err_console
from archdots.ui.progress import progress_decorator
from archdots.core.exceptions import PackageManagerException
from archdots.packages.managers.base import PackageManager
from archdots.packages.managers.custom import Custom
from archdots.utils.decorators import memoize


class WingetResultItem(TypedDict):
    InstalledVersion: str
    Name: str
    Id: str
    IsUpdateAvailable: bool
    Source: str | None
    AvailableVersions: list[str]


class Winget(PackageManager):
    winget_result: list[WingetResultItem] = []

    def __init__(self) -> None:
        super().__init__("winget")

    @progress_decorator("winget packages")
    @memoize
    def get_installed(self, use_memo=False, by_user=True) -> list[str]:
        import json

        process = subprocess.Popen(
            'powershell -Command "Get-WinGetPackage -s winget|where -Property Source -eq "winget"|ConvertTo-Json"',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            shell=True,
            text=True,
            encoding="cp437",
        )

        if not process.stdout:
            if process.stderr:
                err_console.print(process.stderr.read())
            raise PackageManagerException("could not run 'winget list'")

        self.winget_result = json.loads(process.stdout.read())

        pkg_names = [result["Id"] for result in self.winget_result]
        custom_package_names = [pkg.name for pkg in Custom().get_packages(use_memo=use_memo)]
        return list(filter(lambda p: p not in custom_package_names, pkg_names))

    def install(self, packages: list[str], force=True) -> bool:
        if not packages:
            return True
        from os import system

        if not self.winget_result:
            self.get_installed()

        id_by_name = {r["Name"]: r["Id"] for r in self.winget_result}

        error_happened = False
        for package in packages:
            if package in id_by_name:
                package = id_by_name[package]
            error_happened = (
                error_happened
                or system(f'winget install "{package}" --disable-interactivity') != 0
            )
        return not error_happened

    def uninstall(self, packages: list[str]) -> bool:
        if not packages:
            return True
        from os import system

        id_by_name = {r["Name"]: r["Id"] for r in self.winget_result}

        error_happened = False
        for package in packages:
            if package in id_by_name:
                package = id_by_name[package]
            error_happened = (
                error_happened
                or system(f'winget uninstall "{package}" --disable-interactivity') != 0
            )
        return not error_happened

    def is_available(self) -> bool:
        from shutil import which

        return which("winget") is not None
