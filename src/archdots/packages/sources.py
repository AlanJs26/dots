import os
import re
import shutil
from abc import ABC, abstractmethod
from urllib.request import urlretrieve

from archdots.core.exceptions import PackageException
from archdots.utils.validation import is_url_valid


GITHUB_REPO_REGEX = re.compile(
    r"(https?:\/\/)?github\.com\/(?P<user>[^\/]+?)\/(?P<repo>[^\/]+?)(\.git)?\/?$"
)


def _downloaded_file_path(cache_folder: str, source: str) -> str:
    return os.path.join(cache_folder, os.path.basename(source))


def _clone_git_source(cache_folder: str, source: str, downloaded_file: str) -> str:
    basename = downloaded_file.rsplit(".", 1)[0]
    folder_path = os.path.join(cache_folder, basename)
    if os.path.exists(folder_path) and cache_folder in folder_path:
        shutil.rmtree(folder_path)

    os.system(f'git clone "{source}" "{folder_path}"')
    return folder_path


def _extract_tar_source(cache_folder: str, downloaded_file: str, package) -> str:
    import tarfile

    with tarfile.open(downloaded_file) as archive:
        if not (files := archive.getnames()):
            raise PackageException(
                f'Could not extract tar file "{downloaded_file}". Tar file is empty',
                package,
            )

        tar_root = files[0]
        if all(item.startswith(tar_root) for item in files):
            sourced = os.path.join(cache_folder, tar_root)
            archive.extractall(cache_folder, filter="data")
        else:
            sourced = os.path.splitext(downloaded_file)[0]
            os.makedirs(sourced, exist_ok=True)
            archive.extractall(sourced, filter="data")

    os.remove(downloaded_file)
    return sourced


def _extract_zip_source(cache_folder: str, downloaded_file: str, package) -> str:
    from zipfile import ZipFile

    with ZipFile(downloaded_file) as archive:
        if not (files := archive.namelist()):
            raise PackageException(
                f'Could not extract tar file "{downloaded_file}". Tar file is empty',
                package,
            )

        zip_root = files[0]
        if all(item.startswith(zip_root) for item in files):
            sourced = os.path.join(cache_folder, zip_root)
            archive.extractall(cache_folder)
        else:
            sourced = os.path.splitext(downloaded_file)[0]
            os.makedirs(sourced, exist_ok=True)
            archive.extractall(sourced)

    os.remove(downloaded_file)
    return sourced


class SourceHandler(ABC):
    """Base contract for source handlers."""

    @classmethod
    @abstractmethod
    def matches(cls, source: str) -> bool:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def fetch(cls, cache_folder: str, source: str, package) -> str:
        raise NotImplementedError


class GithubRepoSource(SourceHandler):
    """Handle plain GitHub repository URLs by downloading zipball."""

    @classmethod
    def matches(cls, source: str) -> bool:
        return re.match(GITHUB_REPO_REGEX, source) is not None

    @classmethod
    def fetch(cls, cache_folder: str, source: str, package) -> str:
        match = re.match(GITHUB_REPO_REGEX, source)
        if not match:
            raise PackageException(f"{source} is not a valid github repository url", package)

        zipball_source = (
            f"https://api.github.com/repos/{match.group('user')}/"
            f"{match.group('repo')}/zipball"
        )
        return ZipSource.fetch(cache_folder, zipball_source, package)


class GitSource(SourceHandler):
    @classmethod
    def matches(cls, source: str) -> bool:
        return source.endswith(".git")

    @classmethod
    def fetch(cls, cache_folder: str, source: str, package) -> str:
        downloaded_file = _downloaded_file_path(cache_folder, source)
        return _clone_git_source(cache_folder, source, downloaded_file)


class TarGzSource(SourceHandler):
    @classmethod
    def matches(cls, source: str) -> bool:
        return source.endswith(".tar.gz")

    @classmethod
    def fetch(cls, cache_folder: str, source: str, package) -> str:
        downloaded_file = _downloaded_file_path(cache_folder, source)
        urlretrieve(source, downloaded_file)
        return _extract_tar_source(cache_folder, downloaded_file, package)


class ZipSource(SourceHandler):
    @classmethod
    def matches(cls, source: str) -> bool:
        return source.endswith(".zip") or source.endswith("zipball")

    @classmethod
    def fetch(cls, cache_folder: str, source: str, package) -> str:
        downloaded_file = _downloaded_file_path(cache_folder, source)
        urlretrieve(source, downloaded_file)
        return _extract_zip_source(cache_folder, downloaded_file, package)


class DirectDownloadSource(SourceHandler):
    """Fallback handler for plain downloadable files."""

    @classmethod
    def matches(cls, source: str) -> bool:
        return True

    @classmethod
    def fetch(cls, cache_folder: str, source: str, package) -> str:
        downloaded_file = _downloaded_file_path(cache_folder, source)
        urlretrieve(source, downloaded_file)
        return downloaded_file


SOURCE_HANDLERS: tuple[type[SourceHandler], ...] = (
    GithubRepoSource,
    GitSource,
    TarGzSource,
    ZipSource,
    DirectDownloadSource,
)


def fetch_sources(package) -> list[str]:
    """Download and extract package sources into the package cache folder."""
    sourced_paths: list[str] = []

    cache_folder = package.get_cache_folder()
    os.makedirs(cache_folder, exist_ok=True)

    for source in package.source:
        if not is_url_valid(source):
            raise PackageException(f"{source} is not a valid url", package)

        handler = next(
            (source_handler for source_handler in SOURCE_HANDLERS if source_handler.matches(source)),
            None,
        )
        if not handler:
            raise PackageException(f"no source handler found for {source}", package)

        sourced_paths.append(handler.fetch(cache_folder, source, package))

    return sourced_paths
