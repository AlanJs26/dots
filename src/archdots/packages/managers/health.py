from archdots.core.constants import HEALTH_FOLDER
from archdots.ui.progress import progress_decorator
from archdots.core.exceptions import PackageManagerException
from archdots.packages.package import Package, get_packages
from archdots.packages.managers.custom import Custom
from archdots.utils.decorators import memoize


class Health(Custom):
    def __init__(self) -> None:
        super().__init__("health")

    @staticmethod
    def _filter_custom_packages(
        target_pkgs: list[str] | list[Package], all_packages: list[Package]
    ) -> list[Package]:
        if any(isinstance(pkg, Package) for pkg in target_pkgs):
            return target_pkgs  # type: ignore

        filtered_pkgs = list(filter(lambda pkg: pkg.name in target_pkgs, all_packages))
        if len(filtered_pkgs) != len(target_pkgs):
            raise PackageManagerException(
                "the following health scripts do not exist. Either create a PKGBUILD or remove them from config.yaml\n"
                + "  ".join(
                    set(target_pkgs).difference(pkg.name for pkg in all_packages)  # type: ignore
                ),
            )
        return filtered_pkgs

    @memoize
    def get_packages(self, use_memo=False, ignore_platform=False) -> list[Package]:
        return get_packages(HEALTH_FOLDER, ignore_platform)

    @progress_decorator("health scripts")
    @memoize
    def get_installed(self, use_memo=False, by_user=True) -> list[str]:
        health_scripts = self.get_packages()
        return [pkg.name for pkg in health_scripts if pkg.check(supress_output=True)]
