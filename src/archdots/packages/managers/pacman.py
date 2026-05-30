import subprocess

from archdots.ui.console import err_console
from archdots.ui.progress import progress_decorator
from archdots.core.exceptions import PackageManagerException
from archdots.packages.managers.base import PackageManager
from archdots.packages.managers.custom import Custom
from archdots.utils.decorators import memoize


class Pacman(PackageManager):
    def __init__(self, aur_helper="yay") -> None:
        super().__init__("pacman")
        self.aur_helper = aur_helper

    @progress_decorator("pacman packages")
    @memoize
    def get_installed(self, use_memo=False, by_user=True) -> list[str]:
        process = subprocess.Popen(
            f"{self.aur_helper} -Q{'e' if by_user else ''}|awk '{{print $1}}'",
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
            raise PackageManagerException("could not run 'pacman -Qe'")

        pkg_names = [line.strip() for line in process.stdout.readlines()]
        custom_package_names = [pkg.name for pkg in Custom().get_packages(use_memo=use_memo)]
        return list(filter(lambda p: p not in custom_package_names, pkg_names))

    def install(self, packages: list[str], force=True) -> bool:
        if not packages:
            return True
        process = subprocess.Popen(f"{self.aur_helper} -Sy {' '.join(packages)}", shell=True)
        process.communicate()
        return process.returncode == 0

    def uninstall(self, packages: list[str]) -> bool:
        if not packages:
            return True
        process = subprocess.Popen(f"{self.aur_helper} -R {' '.join(packages)}", shell=True)
        process.communicate()
        return process.returncode == 0

    def is_available(self) -> bool:
        from shutil import which

        return which(self.aur_helper.split()[-1]) is not None
