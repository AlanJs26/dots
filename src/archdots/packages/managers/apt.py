import subprocess
from shutil import which

from archdots.ui.progress import progress_decorator
from archdots.packages.managers.base import PackageManager
from archdots.packages.managers.custom import Custom
from archdots.utils.decorators import memoize


class Apt(PackageManager):
    def __init__(self) -> None:
        super().__init__("apt")

    def get_installed(self, use_memo=False, by_user=True) -> list[str]:
        return self._get_installed_cached(use_memo, by_user)

    @memoize
    def _get_installed_cached(self, use_memo: bool, by_user: bool) -> list[str]:
        data = self._get_full_system_data(use_memo)
        return data["user"] if by_user else data["all"]

    @progress_decorator("apt packages")
    @memoize
    def _get_full_system_data(self, use_memo: bool) -> dict[str, list[str]]:
        architecture = self._run_apt("dpkg --print-architecture")
        if len(architecture) > 0:
            architecture = architecture[0]
        else:
            architecture = "amd64"

        # Fetch all
        all_pkgs = [
            p.removesuffix(f":{architecture}")
            for p in self._run_apt("dpkg-query -f '${binary:Package}\n' -W")
        ]
        # Fetch explicitly installed
        user_pkgs = self._run_apt("apt-mark showmanual")

        ignored = self.get_ignored_packages(use_memo=use_memo)

        return {
            "all": [p for p in all_pkgs if p not in ignored],
            "user": [p for p in user_pkgs if p not in ignored],
        }

    def get_ignored_packages(self, use_memo: bool = False) -> set[str]:
        # 1. Ignore Custom packages (PKGBUILDs)
        custom_names = {pkg.name for pkg in Custom().get_packages(use_memo=use_memo)}

        # 2. Ignore Deb packages defined in config
        from archdots.config.manager import ConfigManager

        config = ConfigManager().load(use_cache=use_memo)
        pm_pkgs = config.get("pkgs", {})
        deb_pkgs = pm_pkgs.get("deb", [])
        deb_names = {p.split("@", 1)[0] for p in deb_pkgs if isinstance(p, str)}

        return custom_names | deb_names

    def _run_apt(self, command: str) -> list[str]:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            text=True,
        )
        stdout_data, _ = process.communicate()
        if process.returncode != 0:
            return []
        return [line.strip() for line in stdout_data.splitlines() if line.strip()]

    def install(self, packages: list[str], force=True) -> bool:
        if not packages:
            return True
        process = subprocess.Popen(
            f"sudo apt-get install -y {' '.join(packages)}", shell=True
        )
        process.communicate()
        return process.returncode == 0

    def uninstall(self, packages: list[str]) -> bool:
        if not packages:
            return True
        process = subprocess.Popen(
            f"sudo apt-get remove -y {' '.join(packages)}", shell=True
        )
        process.communicate()
        return process.returncode == 0

    def is_available(self) -> bool:
        return which("apt-get") is not None
