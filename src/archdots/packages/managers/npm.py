import json
import subprocess
from shutil import which

from archdots.ui.console import err_console
from archdots.ui.progress import progress_decorator
from archdots.core.exceptions import PackageManagerException
from archdots.packages.managers.base import PackageManager
from archdots.packages.managers.custom import Custom
from archdots.utils.decorators import memoize


class Npm(PackageManager):
    def __init__(self) -> None:
        super().__init__("npm")

    def get_installed(self, use_memo=False, by_user=True) -> list[str]:
        pkg_names = self._get_all_installed(use_memo)

        # Usually npm and corepack are installed globally by default, we can exclude them if by_user is True
        if by_user:
            pkg_names = [p for p in pkg_names if p not in ["npm", "corepack"]]

        return pkg_names

    @progress_decorator("npm packages")
    @memoize
    def _get_all_installed(self, use_memo: bool = False) -> list[str]:
        command = "npm list -g --depth=0 --json"
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            text=True,
        )

        stdout_data, stderr_data = process.communicate()
        
        try:
            data = json.loads(stdout_data)
        except json.JSONDecodeError:
            if stderr_data:
                err_console.print(stderr_data)
            raise PackageManagerException(f"could not parse json from '{command}'")

        dependencies = data.get("dependencies", {})
        pkg_names = list(dependencies.keys())

        custom_package_names = [pkg.name for pkg in Custom().get_packages(use_memo=use_memo)]
        return list(filter(lambda p: p not in custom_package_names, pkg_names))

    def install(self, packages: list[str], force=True) -> bool:
        if not packages:
            return True
        process = subprocess.Popen(f"npm install -g {' '.join(packages)}", shell=True)
        process.communicate()
        return process.returncode == 0

    def uninstall(self, packages: list[str]) -> bool:
        if not packages:
            return True
        process = subprocess.Popen(f"npm uninstall -g {' '.join(packages)}", shell=True)
        process.communicate()
        return process.returncode == 0

    def is_available(self) -> bool:
        return which("npm") is not None
