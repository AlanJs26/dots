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

    @progress_decorator("npm packages")
    @memoize
    def get_installed(self, use_memo=False, by_user=True) -> list[str]:
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

        # Usually npm and corepack are installed globally by default, we can exclude them if by_user is True
        if by_user:
            for default_pkg in ["npm", "corepack"]:
                if default_pkg in pkg_names:
                    pkg_names.remove(default_pkg)

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
