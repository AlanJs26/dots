import os
import re
import shutil
from pathlib import Path
from urllib.request import urlretrieve

from archdots.core.exceptions import PackageException
from archdots.utils.validation import is_url_valid


def fetch_sources(package) -> list[str]:
    """Download and extract package sources into the package cache folder."""
    sourced_folders: list[str] = []

    os.makedirs(package.get_cache_folder(), exist_ok=True)
    for source in package.source:
        if not is_url_valid(source):
            raise PackageException(f"{source} is not a valid url", package)

        github_regex = re.compile(
            r"(https?:\/\/)?github\.com\/(?P<user>[^\/]+?)\/(?P<repo>[^\/]+?)(\.git)?\/?$"
        )
        if match := re.match(github_regex, source):
            source = (
                f"https://api.github.com/repos/{match.group('user')}/"
                f"{match.group('repo')}/zipball"
            )

        downloaded_file = os.path.join(package.get_cache_folder(), os.path.basename(source))
        sourced = downloaded_file

        if source.endswith(".git"):
            basename = downloaded_file.rsplit(".", 1)[0]
            folder_path = os.path.join(package.get_cache_folder(), basename)
            if os.path.exists(folder_path) and package.get_cache_folder() in folder_path:
                shutil.rmtree(folder_path)

            os.system(f'git clone "{source}" "{folder_path}"')
            sourced = folder_path
        elif source.endswith(".tar.gz"):
            urlretrieve(source, downloaded_file)

            import tarfile

            with tarfile.open(downloaded_file) as f:
                if not (files := f.getnames()):
                    raise PackageException(
                        f'Could not extract tar file "{downloaded_file}". Tar file is empty',
                        package,
                    )
                tar_root = files[0]
                if all(item.startswith(tar_root) for item in files):
                    sourced = os.path.join(package.get_cache_folder(), tar_root)
                    f.extractall(package.get_cache_folder(), filter="data")
                else:
                    sourced = os.path.splitext(downloaded_file)[0]
                    os.makedirs(sourced, exist_ok=True)
                    f.extractall(sourced, filter="data")

            os.remove(downloaded_file)
        elif source.endswith(".zip") or source.endswith("zipball"):
            urlretrieve(source, downloaded_file)

            from zipfile import ZipFile

            with ZipFile(downloaded_file) as f:
                if not (files := f.namelist()):
                    raise PackageException(
                        f'Could not extract tar file "{downloaded_file}". Tar file is empty',
                        package,
                    )
                zip_root = files[0]
                if all(item.startswith(zip_root) for item in files):
                    sourced = os.path.join(package.get_cache_folder(), zip_root)
                    f.extractall(package.get_cache_folder())
                else:
                    sourced = os.path.splitext(downloaded_file)[0]
                    os.makedirs(sourced, exist_ok=True)
                    f.extractall(sourced)

            os.remove(downloaded_file)
        else:
            urlretrieve(source, downloaded_file)

        sourced_folders.append(sourced)

    return sourced_folders
