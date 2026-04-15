import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from archdots.core.constants import CACHE_FOLDER
from archdots.core.exceptions import PackageException
from archdots.packages import lifecycle as pkg_lifecycle
from archdots.packages import parser as pkg_parser
from archdots.packages import sources as pkg_sources
from archdots.utils.validation import is_url_valid


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
    source_on_check: bool = False

    def __post_init__(self):
        if not self.name or not self.description:
            raise PackageException("all packages must have a name and description")

        for dep in self.depends:
            if ":" not in dep:
                raise PackageException(
                    f"Invalid dependency: {dep}\n\nall dependencies in must have a package manager specifier",
                    self,
                )

        if ":" in self.name:
            raise PackageException(": are not allowed in package names", self)

        if self.url and not is_url_valid(self.url):
            raise PackageException(f'url "{self.url}" is bad formated', self)
        if self.source and (not all(is_url_valid(source) for source in self.source)):
            raise PackageException(f"invalid source(s)\nsources: {self.source}", self)

    def __hash__(self) -> int:
        return hash(self.name)

    def fetch_sources(self):
        return pkg_sources.fetch_sources(self)

    def _run_pkgbuild_function(self, name, supress_output=False, sources: list[str] = []):
        return pkg_lifecycle.run_pkgbuild_function(self, name, supress_output, sources)

    def check(self, supress_output=False):
        return pkg_lifecycle.check(self, supress_output)

    def update(self, supress_output=False, force=False):
        return pkg_lifecycle.update(self, supress_output, force)

    def install(self, supress_output=False, force=False):
        return pkg_lifecycle.install(self, supress_output, force)

    def uninstall(self, supress_output=False, force=False):
        return pkg_lifecycle.uninstall(self, supress_output, force)

    def get_cache_folder(self):
        return os.path.join(CACHE_FOLDER, self.name)


def get_packages(folder: str | Path, ignore_platform=False) -> list[Package]:
    return pkg_parser.get_packages(
        folder,
        package_from_path_fn=lambda path: package_from_path(path),
        ignore_platform=ignore_platform,
    )


def parse_package_bash(pkgbuild_path: str | Path) -> tuple[dict[str, Any], list[str]]:
    return pkg_parser.parse_package_bash(pkgbuild_path)


def parse_package_lark(pkgbuild_path: str | Path) -> tuple[dict[str, Any], list[str]]:
    return pkg_parser.parse_package_lark(pkgbuild_path)


def package_from_path(folder_path: str | Path) -> Package:
    return pkg_parser.package_from_path(folder_path, Package)


__all__ = [
    "Package",
    "get_packages",
    "parse_package_bash",
    "parse_package_lark",
    "package_from_path",
]
