import subprocess
from abc import abstractmethod
from typing import Iterable
from itertools import chain, groupby
from archdots.exceptions import PackageManagerException, PackageException
from archdots.package import get_packages, Package
from archdots.utils import memoize, SingletonMeta
from archdots.constants import PACKAGES_FOLDER


class PackageManager(metaclass=SingletonMeta):
    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def install(self, packages: list[str]) -> bool:
        raise NotImplemented

    @abstractmethod
    def uninstall(self, packages: list[str]) -> bool:
        raise NotImplemented

    @abstractmethod
    def is_available(self) -> bool:
        raise NotImplemented

    @abstractmethod
    def get_installed(self, use_memo=False) -> list[str]:
        raise NotImplemented


def split_packages_by_pm(packages: list[str]) -> dict[PackageManager, list[str]]:
    pkgs_by_pm: dict[PackageManager, list[str]] = {
        next(filter(lambda pm: pm.name == package_manager, package_managers)): [
            pkg.split(":")[1] for pkg in pkgs
        ]
        for package_manager, pkgs in groupby(packages, lambda x: x.split(":")[0])
    }
    return pkgs_by_pm


def split_external_dependencies(
    packages: list[Package], all_packages: list[Package]
) -> tuple[dict[PackageManager, list[str]], list[Package]]:
    """
    given a list of target packages and a list of all packages available, returns a dictionary grouping all external dependencies by its package manager and a list of packages sorted by dependency order
    """

    def sort_packages(packages: list[Package]) -> list[Package]:
        """
        Sorts packages by dependencies. less dependency to greater dependency
        """
        history: list[Package] = []

        priority_dict: dict[Package, int] = {package: 1 for package in packages}

        def filter_custom_packages(depends: list[str]) -> list[Package]:
            return list(filter(lambda package: package.name in depends, packages))

        def give_priority(package: Package, traceback=[]) -> int:
            local_dependencies = filter_custom_packages(package.depends)

            if not local_dependencies or package in history:
                history.append(package)
                return priority_dict[package]
            if priority_dict[package] == -1:
                raise PackageException(
                    f"circular dependency detected: {' → '.join(p.name for p in traceback)}"
                )

            priority_dict[package] = -1
            computed_priority = (
                max(
                    give_priority(dep, traceback + [package])
                    for dep in local_dependencies
                )
                + 1
            )

            priority_dict[package] = computed_priority
            history.append(package)

            return computed_priority

        for package in priority_dict:
            give_priority(package)

        return sorted(priority_dict, key=lambda x: priority_dict[x])

    # given a list of dependencies returns local packages only
    def filter_local_packages(depends: list[str]) -> Iterable[Package]:
        return filter(
            lambda package: ("custom:" + package.name in depends)
            or (package.name in depends),
            all_packages,
        )

    # all local packages listed as dependencies of "packages"
    dependencies = list(
        chain.from_iterable(
            filter_local_packages(package.depends) for package in packages
        )
    )

    # sorts packages and dependencies (no duplicates) by dependency priority
    sorted_packages = sort_packages(list(set(packages + dependencies)))

    # get all external depencies (need a package manager) and raise error on invalid dependencies
    external_dependencies = _get_external_dependencies(sorted_packages)

    # build a dict grouping dependencies by package manager.
    ext_dependencies_by_pm = split_packages_by_pm(external_dependencies)

    return ext_dependencies_by_pm, sorted_packages


def _get_external_dependencies(packages: list[Package]) -> list[str]:
    """
    get all external dependencies (when package manager is needed) and raise an error on invalid dependencies
    """

    packages_names = [package.name for package in packages]

    def filter_external_packages(depends: list[str]) -> Iterable[str]:
        return filter(lambda dep: dep not in packages_names, depends)

    pm_names = [pm.name for pm in package_managers]

    dependencies = []
    for package in packages:
        external_dependencies = filter_external_packages(package.depends)
        for dep in external_dependencies:
            if ":" not in dep:
                raise PackageException(
                    f"""invalid dependency of "{package.name}": "{dep}"
                    {dep} is not a custom package
                    missing package_manager especifier. i.e. "package_manager:{dep}"
                    valid package_managers: {', '.join('"' + n + '"' for n in pm_names)}"""
                )
            elif dep.split(":")[0] not in pm_names:
                raise PackageException(
                    f"""invalid package manager of "{dep}": "{dep.split(':')[0]}"
                    valid package_managers: {', '.join('"' + n + '"' for n in pm_names)}"""
                )
            dependencies.append(dep)

    return dependencies


def are_custom_packages_valid(packages: list[Package]):
    """
    given a list of packages, checks if all packages have correct dependencies.
    raises an Exception in case of invalid packages
    """
    split_external_dependencies(packages, packages)
    return True


class Custom(PackageManager):
    def __init__(self) -> None:
        super().__init__("custom")

    @staticmethod
    def _filter_custom_packages(
        target_pkgs: list[str] | list[Package], all_packages: list[Package]
    ) -> list[Package]:
        if any(isinstance(pkg, Package) for pkg in target_pkgs):
            return target_pkgs  # type: ignore
        else:
            return list(filter(lambda pkg: pkg.name in target_pkgs, all_packages))

    @memoize
    def get_packages(self, use_memo=False) -> list[Package]:
        return get_packages(PACKAGES_FOLDER)

    @memoize
    def get_installed(self, use_memo=False) -> list[str]:
        custom_packages = self.get_packages()

        return [pkg.name for pkg in custom_packages if pkg.check(supress_output=True)]

    def install(self, packages: list[str] | list[Package]) -> bool:
        all_packages = self.get_packages()
        filtered_packages = self._filter_custom_packages(packages, all_packages)

        ext_dependencies_by_pm, sorted_packages = split_external_dependencies(
            filtered_packages, all_packages
        )

        for pm in ext_dependencies_by_pm:
            # filter out dependencies that are already installed
            deps = list(
                set(ext_dependencies_by_pm[pm]).difference(set(pm.get_installed()))
            )
            if not deps:
                continue
            pm.install(deps)

        for package in sorted_packages:
            package.install()

        return True

    def uninstall(self, packages: list[str] | list[Package]) -> bool:
        all_packages = self.get_packages()
        filtered_packages = self._filter_custom_packages(packages, all_packages)

        ext_dependencies_by_pm, sorted_packages = split_external_dependencies(
            filtered_packages, all_packages
        )

        for pm in ext_dependencies_by_pm:
            # filter out dependencies that are already installed
            deps = list(
                set(ext_dependencies_by_pm[pm]).difference(set(pm.get_installed()))
            )
            if not deps:
                continue
            pm.uninstall(deps)

        for package in sorted_packages:
            package.uninstall()

        return True

    def check_packages(self, packages: list[Package]) -> dict[Package, bool]:
        return {package: package.check() for package in packages}

    def is_available(self) -> bool:
        return True


class Pacman(PackageManager):
    def __init__(self, aur_helper="yay") -> None:
        super().__init__("pacman")
        self.aur_helper = aur_helper

    @memoize
    def get_installed(self, use_memo=False) -> list[str]:
        process = subprocess.Popen(
            f"{self.aur_helper} -Qe|awk '{{print $1}}'",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            shell=True,
            text=True,
        )
        if not process.stdout:
            if process.stderr:
                print(process.stderr.read())
            raise PackageManagerException("could not run 'pacman -Qe'")

        return [line.strip() for line in process.stdout.readlines()]

    def install(self, packages: list[str]) -> bool:
        process = subprocess.Popen(
            f"{self.aur_helper} -Sy {' '.join(packages)}", shell=True
        )
        process.communicate()
        return process.returncode == 0

    def uninstall(self, packages: list[str]) -> bool:
        process = subprocess.Popen(
            f"{self.aur_helper} -R {' '.join(packages)}", shell=True
        )
        process.communicate()
        return process.returncode == 0

    def is_available(self) -> bool:
        from shutil import which

        return which(self.aur_helper.split()[-1]) is not None


package_managers: list[PackageManager] = [Pacman(), Custom()]


def check_packages(packages: list[str], use_memo=False) -> dict[str, bool]:
    pkgs_by_pm = split_packages_by_pm(packages)

    statuses = {}
    for pm, pkgs in pkgs_by_pm.items():
        for pkg in pkgs:
            statuses[pkg] = pkg in pm.get_installed(use_memo)

    return statuses
