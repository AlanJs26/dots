import os
import shutil
import subprocess
from typing import Any
import re
from dataclasses import dataclass
from archdots.constants import CACHE_FOLDER, PLATFORM, PLATFORM
from archdots.utils import is_url_valid
from archdots.exceptions import PackageException
from pathlib import Path


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

            if source.endswith(".git"):
                basename = downloaded_file.rsplit(".", 1)[0]
                folder_path = os.path.join(self.get_cache_folder(), basename)
                if (
                    os.path.exists(folder_path)
                    and self.get_cache_folder() in folder_path
                ):
                    shutil.rmtree(folder_path)

                os.system(f'git clone "{source}" "{folder_path}"')
                sourced = folder_path
            elif source.endswith(".tar.gz"):
                # download source inside cache folder
                urlretrieve(source, downloaded_file)

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
                # download source inside cache folder
                urlretrieve(source, downloaded_file)

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

        if PLATFORM == "linux":
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
        else:
            hashtable = ""
            if sources:
                hashtable = "$sourced = @{\n"
                for i, folder in enumerate(sources):
                    hashtable += f'"{i}" = "{folder}"\n'
                hashtable += "}"

            from archdots.package_parser import parser, PackageTransformer, Function

            with open(self.pkgbuild, "r") as f:
                text = f.read()
            tree = parser.parse(text)
            parsed_functions: list[Function] = [
                f
                for f in PackageTransformer().transform(tree)
                if isinstance(f, Function)
            ]

            found_function = next(
                filter(
                    lambda item: item.name == name,
                    parsed_functions,
                ),
                None,
            )
            if not found_function:
                raise PackageException(
                    f'tried to executed an unknown PKGBUILD function "{found_function}"',
                    self,
                )

            command = f"""
            $PKGPATH = "{os.path.dirname(self.pkgbuild)}"
            {hashtable}
            {found_function.content}
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


def parse_package_bash(pkgbuild_path: str | Path) -> tuple[dict[str, Any], list[str]]:
    pkgbuild_path = Path(pkgbuild_path)
    pkg_name = pkgbuild_path.parent.stem

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
    source {pkgbuild_path}
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
            "could not read PKGBUILD", pkg_name=pkg_name, pkgbuild=str(pkgbuild_path)
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
    funcs = list(filter(str, func_text.splitlines()))

    return fields_dict, funcs


def parse_package_lark(pkgbuild_path: str | Path) -> tuple[dict[str, Any], list[str]]:
    from archdots.package_parser import parser, PackageTransformer, Function, Item

    with open(pkgbuild_path, "r") as f:
        text = f.read()
    tree = parser.parse(text)
    parsed_items: list[Function | Item] = PackageTransformer().transform(tree)

    fields_dict = {
        item.key: str(item.value) for item in parsed_items if isinstance(item, Item)
    }
    funcs = [func.name for func in parsed_items if isinstance(func, Function)]

    return fields_dict, funcs


def package_from_path(folder_path: str | Path) -> Package:
    """
    given a path to a folder that contains a PKGBUILD, run it and extract all desired fields.
    raise an error when there is some funciton/field missing.
    """
    folder_path = Path(folder_path)
    pkg_name = folder_path.stem
    pkgbuild_path = folder_path / "PKGBUILD"

    if PLATFORM == "linux":
        fields_dict, funcs = parse_package_bash(pkgbuild_path)
    else:
        fields_dict, funcs = parse_package_lark(pkgbuild_path)

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

    if missing_fields := set(known_fields).difference(fields_dict.keys()):
        raise PackageException(
            f"missing fields: {list(missing_fields)}",
            pkg_name=pkg_name,
            pkgbuild=str(pkgbuild_path),
        )
    if missing_funcs := set(known_funcs).difference(funcs):
        raise PackageException(
            f"missing functions: {list(missing_funcs)}",
            pkg_name=pkg_name,
            pkgbuild=str(pkgbuild_path),
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
            pkgbuild=str(pkgbuild_path),
        )

    return Package(
        name=pkg_name,
        pkgbuild=str(pkgbuild_path),
        available_functions=funcs,
        **fields_dict,
    )
