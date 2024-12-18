import os
import subprocess
from typing import Any, Iterable
import re
from src.package_manager import package_managers, PackageManager
from itertools import chain, groupby
from dataclasses import dataclass
from src.constants import CACHE_FOLDER


@dataclass
class Package:
    name: str
    description: str
    url: str
    depends: list[str]
    source: list[str]
    pkgbuild: str
    available_functions: list[str]

    def __hash__(self) -> int:
        return hash(self.name)

    def fetch_sources(self):
        """
        download and extract (when needed) all sources in CACHE_FOLDER/self.name
        """
        os.makedirs(self.get_cache_folder(), exist_ok=True)
        for source in self.source:
            downloaded_file = os.path.join(
                self.get_cache_folder(), os.path.basename(source)
            )
            os.system(f'wget "{source}" -P "{self.get_cache_folder()}"')
            if source.endswith(".tar.gz"):
                os.system(
                    f'tar -xvf "{downloaded_file}" -C "{self.get_cache_folder()}"'
                )
                os.system(f'rm "{downloaded_file}"')
            elif source.endswith(".zip"):
                os.system(f'unzip "{downloaded_file}" -d "{self.get_cache_folder()}"')
                os.system(f'rm "{downloaded_file}"')

    def _run_pkgbuild_function(self, name, supress_output=False):
        os.makedirs(self.get_cache_folder(), exist_ok=True)
        command = f"""
        source {os.path.abspath(self.pkgbuild)}
        {name}
        """

        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.DEVNULL if supress_output else None,
            stderr=subprocess.DEVNULL if supress_output else None,
            cwd=self.get_cache_folder(),
        )

        process.communicate()

        return process.returncode

    def check(self, supress_output=False):
        return self._run_pkgbuild_function("check", supress_output) == 0

    def update(self, supress_output=False):
        if self.check(supress_output) and "install" not in self.available_functions:
            print("already installed")
            return
        return self._run_pkgbuild_function("update", supress_output) == 0

    def install(self, supress_output=False):
        if self.check(supress_output):
            print("already installed")
            return

        return self._run_pkgbuild_function("install", supress_output) == 0

    def uninstall(self, supress_output=False):
        if not self.check(supress_output):
            print("not installed. Cannot uninstall")
            return

        return self._run_pkgbuild_function("uninstall", supress_output) == 0

    def get_cache_folder(self):
        return os.path.join(CACHE_FOLDER, self.name)


class PackageException(Exception):
    def __init__(self, message) -> None:
        super().__init__(re.sub(r"^\s+", "", message, flags=re.MULTILINE))


def get_packages(folder) -> list[Package]:
    """
    returns all packages inside folder (valid packages contains a PKGBUILD)
    """

    filtered_packages = list(
        filter(
            lambda x: "PKGBUILD" in os.listdir(os.path.join(folder, x)),
            os.listdir(folder),
        )
    )
    return [
        package_from_path(os.path.join(folder, package_name))
        for package_name in filtered_packages
    ]


def package_from_path(path) -> Package:
    """
    given a path to a folder that contains a PKGBUILD, run it and extract all desired fields.
    raise an error when there is some funciton/field missing.
    """
    known_fields = [
        "depends",
        "description",
        "source",
        "url",
    ]
    known_funcs = [
        "check",
        "install",
        "uninstall",
    ]
    command = f"""
    prev="$(declare -p)"
    source {path}/PKGBUILD
    diff <(cat<<<$prev) <(declare -p) |cut -d' ' -f4-|grep -E '^({'|'.join(known_fields)})'
    echo ===
    declare -F|cut -d' ' -f3-|grep -E '^({'|'.join(known_funcs)})'
    """

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
        shell=True,
        text=True,
    )
    if not process.stdout:
        raise PackageException("could not read PKGBUILD")

    vars_text, func_text, *_ = process.stdout.read().split("===")

    def parse_value(value) -> str | list[str]:
        """
        convert bash-style variables into text
        """
        string_regex = re.compile(r'^"(.+)"$')
        array_regex = re.compile(r'\[[0-9]\]="(.+?)"')
        if re.match(string_regex, value):
            return re.findall(string_regex, value)[0].strip()
        else:
            return re.findall(array_regex, value)

    fields = re.findall(r"^(\w+?)=(.+)\n", vars_text, flags=re.MULTILINE)
    fields_dict: dict[str, Any] = {key: parse_value(value) for key, value in fields}

    missing_fields = list(set(known_fields).difference(fields_dict.keys()))
    if missing_fields:
        raise PackageException(f"missing fields: {missing_fields}")

    # filter out empty strings
    funcs = list(filter(str, func_text.splitlines()))

    missing_funcs = list(set(known_funcs).difference(funcs))
    if missing_funcs:
        raise PackageException(f"missing functions: {missing_funcs}")

    return Package(
        name=os.path.basename(path),
        pkgbuild=os.path.join(path, "PKGBUILD"),
        available_functions=funcs,
        **fields_dict,
    )


def sort_packages(packages: list[Package]) -> list[Package]:
    """
    Sorts packages by dependencies. less dependency to greater dependency
    """
    history: list[Package] = []

    priority_dict: dict[Package, int] = {package: 1 for package in packages}

    def filter_local_packages(depends: list[str]) -> list[Package]:
        return list(filter(lambda package: package.name in depends, packages))

    def give_priority(package: Package, traceback=[]) -> int:
        local_dependencies = filter_local_packages(package.depends)

        if not local_dependencies or package in history:
            history.append(package)
            return priority_dict[package]
        if priority_dict[package] == -1:
            raise PackageException(
                f"circular dependency detected: {' → '.join(p.name for p in traceback)}"
            )

        priority_dict[package] = -1
        computed_priority = (
            max(give_priority(dep, traceback + [package]) for dep in local_dependencies)
            + 1
        )

        priority_dict[package] = computed_priority
        history.append(package)

        return computed_priority

    for package in priority_dict:
        give_priority(package)

    return sorted(priority_dict, key=lambda x: priority_dict[x])


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


def is_package_valid(packages: list[Package]):
    """
    given a list of packages, checks if all packages have correct dependencies.
    raises an Exception in case of invalid packages
    """
    split_external_dependencies(packages, packages)
    return True


def split_external_dependencies(
    packages: list[Package], all_packages: list[Package]
) -> tuple[dict[PackageManager, list[str]], list[Package]]:
    """
    given a list of target packages and a list of all packages available, returns a dictionary grouping all external dependencies by its package manager and a list of packages sorted by dependency order
    """

    # given a list of dependencies returns local packages only
    def filter_local_packages(depends: list[str]) -> Iterable[Package]:
        return filter(lambda package: package.name in depends, all_packages)

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
    ext_dependencies_by_pm: dict[PackageManager, list[str]] = {
        next(filter(lambda pm: pm.name == package_manager, package_managers)): [
            dep.split(":")[1] for dep in dependencies
        ]
        for package_manager, dependencies in groupby(
            external_dependencies, lambda x: x.split(":")[0]
        )
    }
    return ext_dependencies_by_pm, sorted_packages


def install_packages(packages: list[Package], all_packages: list[Package]):
    ext_dependencies_by_pm, sorted_packages = split_external_dependencies(
        packages, all_packages
    )

    for pm in ext_dependencies_by_pm:
        # filter out dependencies that are already installed
        deps = list(set(ext_dependencies_by_pm[pm]).difference(set(pm.get_installed())))
        if not deps:
            continue
        pm.install(deps)

    for package in sorted_packages:
        package.install()


def uninstall_packages(packages: list[Package], all_packages: list[Package]):
    ext_dependencies_by_pm, sorted_packages = split_external_dependencies(
        packages, all_packages
    )

    for pm in ext_dependencies_by_pm:
        # filter out dependencies that are already installed
        deps = list(set(ext_dependencies_by_pm[pm]).difference(set(pm.get_installed())))
        if not deps:
            continue
        pm.uninstall(deps)

    for package in sorted_packages:
        package.uninstall()


def check_packages(packages: list[Package]) -> dict[Package, bool]:
    return {package: package.check() for package in packages}
