import subprocess
from shutil import which

from archdots.ui.console import err_console
from archdots.ui.progress import progress_decorator
from archdots.core.exceptions import PackageManagerException
from archdots.packages.managers.base import PackageManager
from archdots.packages.managers.custom import Custom
from archdots.utils.decorators import memoize


class Apt(PackageManager):
    def __init__(self) -> None:
        super().__init__("apt")

    @progress_decorator("apt packages")
    @memoize
    def get_installed(self, use_memo=False, by_user=True) -> list[str]:
        command = "apt-mark showmanual" if by_user else "dpkg-query -f '${binary:Package}\n' -W"
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            text=True,
        )

        stdout_data, stderr_data = process.communicate()
        
        if process.returncode != 0:
            if stderr_data:
                err_console.print(stderr_data)
            raise PackageManagerException(f"could not run '{command}'")

        pkg_names = [line.strip() for line in stdout_data.splitlines() if line.strip()]
        custom_package_names = [pkg.name for pkg in Custom().get_packages(use_memo=use_memo)]
        return list(filter(lambda p: p not in custom_package_names, pkg_names))

    def install(self, packages: list[str], force=True) -> bool:
        if not packages:
            return True
        process = subprocess.Popen(f"sudo apt-get install -y {' '.join(packages)}", shell=True)
        process.communicate()
        return process.returncode == 0

    def uninstall(self, packages: list[str]) -> bool:
        if not packages:
            return True
        process = subprocess.Popen(f"sudo apt-get remove -y {' '.join(packages)}", shell=True)
        process.communicate()
        return process.returncode == 0

    def is_available(self) -> bool:
        return which("apt-get") is not None
