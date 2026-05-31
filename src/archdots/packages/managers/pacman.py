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

    def get_installed(self, use_memo=False, by_user=True) -> list[str]:
        # all_installed = self._get_all_installed(use_memo)
        
        # In pacman, we distinguish by_user (explicitly installed) 
        # from the full list. Our internal method fetches both once if needed.
        # But for pacman, it's easier to fetch based on what's requested.
        # However, to avoid two passes, let's fetch everything and filter.
        
        # Actually, let's simplify: if we want to avoid two passes, 
        # we MUST fetch the superset (all packages) once.
        
        # Note: the original code called -Qe for by_user=True.
        # Let's refactor to fetch all and explicitly installed once.
        return self._get_installed_cached(use_memo, by_user)

    @memoize
    def _get_installed_cached(self, use_memo: bool, by_user: bool) -> list[str]:
        # We still have the problem that by_user=True and by_user=False are different keys.
        # Solution: use a single internal method that fetches BOTH and caches them in a single dict.
        data = self._get_full_system_data(use_memo)
        return data["user"] if by_user else data["all"]

    @progress_decorator("pacman packages")
    @memoize
    def _get_full_system_data(self, use_memo: bool) -> dict[str, list[str]]:
        # Fetch all
        all_pkgs = self._run_pacman("-Q")
        # Fetch explicitly installed
        user_pkgs = self._run_pacman("-Qe")
        
        custom_package_names = [pkg.name for pkg in Custom().get_packages(use_memo=use_memo)]
        
        return {
            "all": [p for p in all_pkgs if p not in custom_package_names],
            "user": [p for p in user_pkgs if p not in custom_package_names]
        }

    def _run_pacman(self, args: str) -> list[str]:
        process = subprocess.Popen(
            f"{self.aur_helper} {args}|awk '{{print $1}}'",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            shell=True,
            text=True,
            encoding="cp437",
        )
        if not process.stdout:
            return []
        return [line.strip() for line in process.stdout.readlines()]

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
