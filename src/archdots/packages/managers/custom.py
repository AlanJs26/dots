import subprocess

from archdots.core.constants import PACKAGES_FOLDER
from archdots.ui.progress import progress_decorator
from archdots.core.exceptions import PackageManagerException
from archdots.packages.package import Package, get_packages
from archdots.packages.dependencies import split_external_dependencies
from archdots.packages.managers.base import PackageManager
from archdots.config.manager import ConfigManager
from archdots.utils.decorators import memoize


class Custom(PackageManager):
    def __init__(self, name: str = "custom") -> None:
        super().__init__(name)

    @staticmethod
    def _filter_custom_packages(
        target_pkgs: list[str] | list[Package], all_packages: list[Package]
    ) -> list[Package]:
        if any(isinstance(pkg, Package) for pkg in target_pkgs):
            return target_pkgs  # type: ignore

        filtered_pkgs = list(filter(lambda pkg: pkg.name in target_pkgs, all_packages))
        if len(filtered_pkgs) != len(target_pkgs):
            raise PackageManagerException(
                "the following custom packages does not exist. Either create a PKGBUILD or remove them from config.yaml\n"
                + "  ".join(
                    set(target_pkgs).difference(pkg.name for pkg in all_packages)  # type: ignore
                ),
            )
        return filtered_pkgs

    @progress_decorator("custom packages")
    @memoize
    def _get_all_packages(self, use_memo=False) -> list[Package]:
        """Internal memoized method to fetch all packages once."""
        return get_packages(PACKAGES_FOLDER, ignore_platform=False)

    def get_packages(self, use_memo=False, ignore_platform=False) -> list[Package]:
        if ignore_platform:
            return get_packages(PACKAGES_FOLDER, ignore_platform=True)
        return self._get_all_packages(use_memo=use_memo)

    def get_installed(self, use_memo=False, by_user=True) -> list[str]:
        return self._get_installed_cached(use_memo)

    @progress_decorator("custom packages")
    @memoize
    def _get_installed_cached(self, use_memo=False) -> list[str]:
        custom_packages = self.get_packages(use_memo=use_memo)
        return [pkg.name for pkg in custom_packages if pkg.check(supress_output=True)]

    def install(self, packages: list[str] | list[Package], force=True) -> bool:
        if not packages:
            return True

        all_packages = self.get_packages()
        filtered_packages = self._filter_custom_packages(packages, all_packages)

        ext_dependencies_by_pm, sorted_packages = split_external_dependencies(
            filtered_packages, all_packages
        )

        for pm in ext_dependencies_by_pm:
            if pm.name == self.name:
                continue
            deps = set(ext_dependencies_by_pm[pm]).difference(pm.get_installed(by_user=False))
            if deps:
                pm.install(list(deps))

        for package in sorted_packages:
            package.install(force=force)

        return True

    def uninstall(self, packages: list[str] | list[Package]) -> bool:
        if not packages:
            return True

        config = ConfigManager().load()

        all_packages = self.get_packages()
        filtered_packages = self._filter_custom_packages(packages, all_packages)

        ext_dependencies_by_pm, sorted_packages = split_external_dependencies(
            filtered_packages, all_packages
        )

        error_happened = False

        for package in sorted_packages[::-1]:
            if (
                package not in filtered_packages
                and "pkgs" in config
                and self.name in config["pkgs"]
                and package.name in config["pkgs"][self.name]
                or not package.check(True)
            ):
                continue
            package.uninstall()

        for pm in ext_dependencies_by_pm:
            if pm.name == self.name:
                continue

            deps = list(set(ext_dependencies_by_pm[pm]).intersection(pm.get_installed(by_user=False)))

            if "pkgs" in config and pm.name in config["pkgs"]:
                pm_managed_pkgs = config["pkgs"][pm.name]
                deps = list(set(deps).difference(pm_managed_pkgs))

                if pm.name == "pacman":
                    for dep in deps.copy():
                        process = subprocess.Popen(
                            f"LC_ALL=en_US pacman -Qii {dep}|grep 'Required By'",
                            stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL,
                            stdin=subprocess.PIPE,
                            shell=True,
                            text=True,
                        )
                        if not process.stdout:
                            continue
                        stdout = process.stdout.read()
                        required_by = stdout.split(":")
                        if len(required_by) != 2:
                            continue
                        required_by = [item.strip() for item in required_by[1].split("  ")]

                        if set(required_by).intersection(pm_managed_pkgs):
                            deps.remove(dep)

            if deps:
                error_happened = not pm.uninstall(deps) or error_happened

        return not error_happened

    def check_packages(self, packages: list[Package]) -> dict[Package, bool]:
        return {package: package.check() for package in packages}

    def is_available(self) -> bool:
        return True
