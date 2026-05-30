"""Package dependency resolution and management."""

from itertools import chain, groupby
from typing import Iterable

from archdots.core.exceptions import PackageException
from archdots.packages.package import Package
from archdots.packages.managers.base import PackageManager
from archdots.packages.managers.registry import get_package_managers


def split_packages_by_pm(packages: list[str]) -> dict[PackageManager, list[str]]:
    pkgs_by_pm: dict[PackageManager, list[str]] = {}
    normalized = [name if ":" in name else f"custom:{name}" for name in packages]

    package_managers = get_package_managers()
    for package_manager, pkgs in groupby(normalized, lambda name: name.split(":")[0]):
        pm = next(filter(lambda p: p.name == package_manager, package_managers))
        pkgs_by_pm[pm] = [pkg.split(":")[1] for pkg in pkgs]

    return pkgs_by_pm


def split_external_dependencies(
    packages: list[Package], all_packages: list[Package]
) -> tuple[dict[PackageManager, list[str]], list[Package]]:
    """Split dependencies by manager and sort package install order."""

    def sort_packages(items: list[Package]) -> list[Package]:
        history: list[Package] = []
        priority_dict: dict[Package, int] = {package: 1 for package in items}

        def filter_custom_packages(depends: list[str]) -> list[Package]:
            return list(filter(lambda package: package.name in depends, items))

        def give_priority(package: Package, traceback=None) -> int:
            traceback = traceback or []
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
                max(give_priority(dep, traceback + [package]) for dep in local_dependencies) + 1
            )

            priority_dict[package] = computed_priority
            history.append(package)
            return computed_priority

        for package in priority_dict:
            give_priority(package)

        return sorted(priority_dict, key=lambda x: priority_dict[x])

    def filter_local_packages(depends: list[str]) -> Iterable[Package]:
        return filter(
            lambda package: ("custom:" + package.name in depends) or (package.name in depends),
            all_packages,
        )

    dependencies = list(chain.from_iterable(filter_local_packages(pkg.depends) for pkg in packages))
    sorted_packages = sort_packages(list(set(packages + dependencies)))
    external_dependencies = _get_external_dependencies(sorted_packages)
    ext_dependencies_by_pm = split_packages_by_pm(external_dependencies)

    return ext_dependencies_by_pm, sorted_packages


def _get_external_dependencies(packages: list[Package]) -> list[str]:
    packages_names = [package.name for package in packages]

    def filter_external_packages(depends: list[str]) -> Iterable[str]:
        return filter(lambda dep: dep not in packages_names, depends)

    pm_names = [pm.name for pm in get_package_managers()]

    dependencies: list[str] = []
    for package in packages:
        external_dependencies = filter_external_packages(package.depends)
        for dep in external_dependencies:
            if ":" not in dep:
                raise PackageException(
                    f'''invalid dependency of "{package.name}": "{dep}"
                    {dep} is not a custom package
                    missing package_manager especifier. i.e. "package_manager:{dep}"
                    valid package_managers: {', '.join('"' + n + '"' for n in pm_names)}'''
                )
            if dep.split(":")[0] not in pm_names:
                raise PackageException(
                    f'''invalid package manager of "{dep}": "{dep.split(':')[0]}"
                    valid package_managers: {', '.join('"' + n + '"' for n in pm_names)}'''
                )
            dependencies.append(dep)

    return dependencies


def are_custom_packages_valid(packages: list[Package]):
    split_external_dependencies(packages, packages)
    return True
