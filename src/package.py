import os
import subprocess
from typing import Any
import re
from dataclasses import dataclass
from src.constants import CACHE_FOLDER, PLATFORM


@dataclass
class Package:
    name: str
    description: str
    url: str
    depends: list[str]
    source: list[str]
    pkgbuild: str
    available_functions: list[str]
    platform: str = "linux"

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

        return int(process.returncode)

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
    def __init__(self, message, pkg_name="") -> None:
        if pkg_name:
            message = f"Exception for '{pkg_name}' package\n{message}"
        super().__init__(re.sub(r"^\s+", "", message, flags=re.MULTILINE))


def get_packages(folder: str, ignore_platform=False) -> list[Package]:
    """
    returns all packages inside folder (valid packages contains a PKGBUILD)
    """

    filtered_packages = []
    for root, _, files in os.walk(folder, topdown=True):
        if "PKGBUILD" not in files:
            continue
        filtered_packages.append(root)

    packages = [package_from_path(pkgbuild_path) for pkgbuild_path in filtered_packages]
    if ignore_platform:
        return packages
    return list(filter(lambda pkg: PLATFORM == pkg.platform, packages))


def package_from_path(folder_path) -> Package:
    """
    given a path to a folder that contains a PKGBUILD, run it and extract all desired fields.
    raise an error when there is some funciton/field missing.
    """
    pkg_name = os.path.basename(folder_path)
    known_fields = [
        "depends",
        "description",
        "source",
        "url",
    ]
    optional_fields = ["platform"]
    known_funcs = [
        "check",
        "install",
        "uninstall",
    ]
    command = f"""
    prev="$(declare -p)"
    source {folder_path}/PKGBUILD
    diff <(cat<<<$prev) <(declare -p) |cut -d' ' -f4-|grep -E '^({'|'.join([*known_fields, *optional_fields])})'
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
        raise PackageException("could not read PKGBUILD", pkg_name)

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
        raise PackageException(f"missing fields: {missing_fields}", pkg_name)

    # filter out empty strings
    funcs = list(filter(str, func_text.splitlines()))

    missing_funcs = list(set(known_funcs).difference(funcs))
    if missing_funcs:
        raise PackageException(f"missing functions: {missing_funcs}", pkg_name)

    if "platform" in fields_dict and fields_dict["platform"] not in [
        "linux",
        "windows",
    ]:
        raise PackageException(f'invalid platform: {fields_dict["platform"]}', pkg_name)

    return Package(
        name=os.path.basename(folder_path),
        pkgbuild=os.path.join(folder_path, "PKGBUILD"),
        available_functions=funcs,
        **fields_dict,
    )
