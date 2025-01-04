import os
import subprocess
from typing import Any
import re
from dataclasses import dataclass
from archdots.constants import CACHE_FOLDER, PLATFORM
from archdots.utils import is_url_valid
from archdots.exceptions import PackageException


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

    def __post_init__(self):
        if not self.name or not self.description:
            raise PackageException("all packages must have a name and description")
        if not all(":" in dep for dep in self.depends):
            raise PackageException(
                "all dependencies in must have a package manager specifier", self
            )
        if ":" in self.name:
            raise PackageException(": are not allowed in package names", self)

        if self.url and not is_url_valid(self.url):
            raise PackageException(f'url "{self.url}" is bad formated', self)
        if not all(is_url_valid(source) for source in self.source):
            raise PackageException(f"invalid source(s)", self)

    def __hash__(self) -> int:
        return hash(self.name)

    def fetch_sources(self):
        """
        download and extract (when needed) all sources in CACHE_FOLDER/self.name
        """
        from urllib.request import urlretrieve

        sourced_folders: list[str] = []

        os.makedirs(self.get_cache_folder(), exist_ok=True)
        for source in self.source:
            if not is_url_valid(source):
                raise PackageException(f"{source} is not a valid url", self)

            # download github directories as zip
            github_regex = re.compile(
                r"(https?:\/\/)?github\.com\/(?P<user>[^\/]+?)\/(?P<repo>[^\/]+?)\/?$"
            )
            if match := re.match(github_regex, source):
                source = f'https://api.github.com/repos/{match.group("user")}/{match.group("repo")}/zipball'

            # path to source inside cache folder
            downloaded_file = os.path.join(
                self.get_cache_folder(), os.path.basename(source)
            )
            sourced = downloaded_file

            # download source inside cache folder
            urlretrieve(source, downloaded_file)

            # extract source when needed
            if source.endswith(".git"):
                basename = downloaded_file.split(".")[0]
                folder_path = os.path.join(self.get_cache_folder(), basename)

                os.system(f'git clone "{source}" "{folder_path}"')
                sourced = folder_path
            elif source.endswith(".tar.gz"):
                import tarfile

                with tarfile.open(downloaded_file) as f:
                    if not (files := f.getnames()):
                        raise PackageException(
                            f'Could not extract tar file "{downloaded_file}". Tar file is empty',
                            self,
                        )
                    tar_root = files[0]
                    if all(f.startswith(tar_root) for f in files):
                        sourced = os.path.join(self.get_cache_folder(), tar_root)
                        f.extractall(self.get_cache_folder(), filter="data")
                    else:
                        sourced = os.path.splitext(downloaded_file)[0]
                        os.makedirs(sourced, exist_ok=True)
                        f.extractall(sourced, filter="data")

                os.remove(downloaded_file)
            elif source.endswith(".zip") or source.endswith("zipball"):
                from zipfile import ZipFile

                with ZipFile(downloaded_file) as f:
                    if not (files := f.namelist()):
                        raise PackageException(
                            f'Could not extract tar file "{downloaded_file}". Tar file is empty',
                            self,
                        )
                    zip_root = files[0]
                    if all(f.startswith(zip_root) for f in files):
                        sourced = os.path.join(self.get_cache_folder(), zip_root)
                        f.extractall(self.get_cache_folder())
                    else:
                        sourced = os.path.splitext(downloaded_file)[0]
                        os.makedirs(sourced, exist_ok=True)
                        f.extractall(sourced)

                os.remove(downloaded_file)

            sourced_folders.append(sourced)

        return sourced_folders

    def _run_pkgbuild_function(
        self, name, supress_output=False, sources: list[str] = []
    ):
        os.makedirs(self.get_cache_folder(), exist_ok=True)

        bashdict = ""
        if sources:
            for i, folder in enumerate(sources):
                bashdict += f'["{i}"]="{folder}" '
            bashdict = "declare -A sourced=(" + bashdict.strip() + ")"

        command = f"""
        PKGPATH="{os.path.dirname(self.pkgbuild)}"
        {bashdict}
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
        from rich import print

        if not supress_output:
            print(f"[cyan]::[/] Checking")
        return self._run_pkgbuild_function("check", supress_output) == 0

    def update(self, supress_output=False):
        from rich import print

        if not supress_output:
            print(f"[cyan]::[/] Updating [cyan]{self.name}")
        if self.check(supress_output) and "install" not in self.available_functions:
            print(f"[yellow]::[/] {self.name} Already installed")
            return
        sources = self.fetch_sources()
        status = self._run_pkgbuild_function("update", supress_output, sources) == 0
        if status:
            print(f"[green]::[/] Successfully updated [cyan]{self.name}")
        return status

    def install(self, supress_output=False):
        from rich import print

        if not supress_output:
            print(f"[cyan]::[/] Installing [cyan]{self.name}")
        if self.check(supress_output):
            print(f"[yellow]::[/] {self.name} Already installed")
            return

        sources = self.fetch_sources()
        status = self._run_pkgbuild_function("install", supress_output, sources) == 0
        if status:
            print(f"[green]::[/] Successfully installed [cyan]{self.name}")
        return status

    def uninstall(self, supress_output=False):
        from rich import print

        if not supress_output:
            print(f"[cyan]::[/] Uninstalling [cyan]{self.name}")

        if not self.check(supress_output):
            print(f"[red]::[/] {self.name} is not installed. Cannot uninstall")
            return

        status = self._run_pkgbuild_function("uninstall", supress_output) == 0
        if status:
            print(f"[green]::[/] Successfully uninstalled [cyan]{self.name}")
        return status

    def get_cache_folder(self):
        return os.path.join(CACHE_FOLDER, self.name)


def get_packages(folder: str, ignore_platform=False) -> list[Package]:
    """
    returns all packages inside folder (valid packages contains a PKGBUILD)
    """

    filtered_packages = []
    for root, dirs, files in os.walk(folder, topdown=True):
        if "PKGBUILD" not in files:
            continue
        dirs[:] = []
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
        raise PackageException(
            "could not read PKGBUILD",
            pkg_name=pkg_name,
            pkgbuild=folder_path + "/PKGBUILD",
        )

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
        raise PackageException(
            f"missing fields: {missing_fields}",
            pkg_name=pkg_name,
            pkgbuild=folder_path + "/PKGBUILD",
        )

    # filter out empty strings
    funcs = list(filter(str, func_text.splitlines()))

    missing_funcs = list(set(known_funcs).difference(funcs))
    if missing_funcs:
        raise PackageException(
            f"missing functions: {missing_funcs}",
            pkg_name=pkg_name,
            pkgbuild=folder_path + "/PKGBUILD",
        )

    fields_dict["depends"] = [
        ("custom:" + dep if ":" not in dep else dep) for dep in fields_dict["depends"]
    ]

    if "platform" in fields_dict and fields_dict["platform"] not in [
        "linux",
        "windows",
    ]:
        raise PackageException(
            f'invalid platform: {fields_dict["platform"]}',
            pkg_name=pkg_name,
            pkgbuild=folder_path + "/PKGBUILD",
        )

    return Package(
        name=os.path.basename(folder_path),
        pkgbuild=os.path.join(folder_path, "PKGBUILD"),
        available_functions=funcs,
        **fields_dict,
    )
