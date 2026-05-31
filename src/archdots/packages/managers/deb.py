import os
import subprocess
import tempfile
import urllib.request
from shutil import which

from archdots.ui.progress import progress_decorator
from archdots.packages.managers.base import PackageManager
from archdots.utils.decorators import memoize


class Deb(PackageManager):
    """Package manager for .deb files from URLs.
    
    Format: package_name@https://url.com/file.deb
    """

    def __init__(self) -> None:
        super().__init__("deb")

    def get_installed(self, use_memo=False, by_user=True) -> list[str]:
        # During unmanaged/managed filtering, by_user=True is used.
        # We need to return the packages installed via dpkg so they can be
        # correctly prioritized over apt.
        return self._get_installed_cached(use_memo)

    @progress_decorator("deb packages")
    @memoize
    def _get_installed_cached(self, use_memo: bool) -> list[str]:
        command = "dpkg-query -f '${binary:Package}\n' -W"
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            text=True,
        )
        stdout_data, _ = process.communicate()
        if process.returncode != 0:
            return []
        return [line.strip() for line in stdout_data.splitlines() if line.strip()]

    def is_installed(self, package: str, use_memo: bool = False) -> bool:
        name = package.split("@", 1)[0]
        return name in self.get_installed(use_memo, by_user=False)

    def is_installed_in_data(self, package: str, installed_data: list[str]) -> bool:
        name = package.split("@", 1)[0]
        return name in installed_data

    def is_managed(self, installed_pkg: str, configured_pkgs: list[str]) -> bool:
        for conf_pkg in configured_pkgs:
            if conf_pkg.split("@", 1)[0] == installed_pkg:
                return True
        return False

    def install(self, packages: list[str], force=True) -> bool:

        if not packages:
            return True
            
        from archdots.ui.console import err_console
        
        success = True
        for pkg_spec in packages:
            if "@" not in pkg_spec:
                continue
            name, url = pkg_spec.split("@", 1)
            
            if not force and self.is_installed(name):
                continue

            try:
                with tempfile.NamedTemporaryFile(suffix=".deb", delete=False) as tmp:
                    tmp_path = tmp.name
                
                # Download with custom User-Agent
                req = urllib.request.Request(
                    url, 
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                )
                with urllib.request.urlopen(req) as response:
                    with open(tmp_path, 'wb') as out_file:
                        out_file.write(response.read())
                
                # Install using apt-get install to resolve local dependencies
                process = subprocess.Popen(f"sudo apt-get install -y {tmp_path}", shell=True)
                process.communicate()
                
                os.remove(tmp_path)
                
                if process.returncode != 0:
                    success = False
                    err_console.print(f"error: failed to install {name}")
            except Exception as e:
                success = False
                err_console.print(f"error: failed to download or install {name}: {e}")
        
        return success

    @progress_decorator("uninstalling deb packages")
    def uninstall(self, packages: list[str]) -> bool:
        if not packages:
            return True
        names = [pkg.split("@", 1)[0] for pkg in packages]
        process = subprocess.Popen(f"sudo apt-get remove -y {' '.join(names)}", shell=True)
        process.communicate()
        return process.returncode == 0

    def is_available(self) -> bool:
        return which("dpkg") is not None and which("apt-get") is not None
