import subprocess
from shutil import which

from archdots.ui.progress import progress_decorator
from archdots.core.exceptions import PackageManagerException
from archdots.packages.managers.base import PackageManager
from archdots.utils.decorators import memoize


class Uv(PackageManager):
    """Package manager for python tools installed via 'uv tool'."""

    def __init__(self) -> None:
        super().__init__("uv")

    @progress_decorator("uv tools")
    @memoize
    def get_installed(self, use_memo: bool = False, by_user: bool = True) -> list[str]:
        """Get list of installed uv tools.
        
        Note: uv tool list output format is typically:
        package vX.Y.Z [CPython 3.12.1]
        - binary
        """
        process = subprocess.Popen(
            "uv tool list --show-python",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            text=True,
        )

        stdout, stderr = process.communicate()
        if process.returncode != 0:
            if stderr:
                from archdots.ui.console import err_console
                err_console.print(stderr)
            raise PackageManagerException("could not run 'uv tool list'")

        tools = []
        import re
        # Pattern to match: package v1.2.3 [CPython 3.12.1]
        # or just: package v1.2.3
        pkg_pattern = re.compile(r"^([\w-]+)\s+v[\d.]+(?:\s+\[(?:CPython|PyPy)\s+([\d.]+)])?")

        for line in stdout.splitlines():
            line = line.strip()
            if not line or line.startswith("-"):
                continue

            match = pkg_pattern.match(line)
            if match:
                name = match.group(1)
                py_version_full = match.group(2)
                
                if not by_user:
                    tools.append(name)
                
                if py_version_full:
                    # Add major.minor version (e.g. 3.12)
                    version_parts = py_version_full.split(".")
                    if len(version_parts) >= 2:
                        major_minor = f"{version_parts[0]}.{version_parts[1]}"
                        if not by_user:
                            tools.append(f"{name}@{major_minor}")
                        
                        # Most specific version
                        tools.append(f"{name}@{py_version_full}")
                elif by_user:
                    # No version info found, just add name
                    tools.append(name)

        return tools

    def install(self, packages: list[str], force: bool = False) -> bool:
        """Install tools using 'uv tool install'.
        
        Supports optional python version via @ separator (e.g. package@3.12)
        """
        if not packages:
            return True
        
        force_flag = "--force" if force else ""
        
        # Group packages by python version
        install_groups: dict[str | None, list[str]] = {}
        for pkg in packages:
            if "@" in pkg:
                name, version = pkg.split("@", 1)
                if version not in install_groups:
                    install_groups[version] = []
                install_groups[version].append(name)
            else:
                if None not in install_groups:
                    install_groups[None] = []
                install_groups[None].append(pkg)

        success = True
        for version, pkgs in install_groups.items():
            python_flag = f"--python {version}" if version else ""
            cmd = f"uv tool install {force_flag} {python_flag} {' '.join(pkgs)}"
            process = subprocess.Popen(cmd, shell=True)
            process.communicate()
            if process.returncode != 0:
                success = False
        
        return success

    def uninstall(self, packages: list[str]) -> bool:
        """Uninstall tools using 'uv tool uninstall'."""
        if not packages:
            return True
        
        # Clean package names from @version if present
        clean_packages = [pkg.split("@", 1)[0] for pkg in packages]
        
        cmd = f"uv tool uninstall {' '.join(clean_packages)}"
        process = subprocess.Popen(cmd, shell=True)
        process.communicate()
        return process.returncode == 0

    def is_available(self) -> bool:
        """Check if 'uv' is installed."""
        return which("uv") is not None

    def is_managed(self, installed_pkg: str, configured_pkgs: list[str]) -> bool:
        """Check if an installed uv tool is managed by config.
        
        A tool is managed if its name or any of its versioned aliases are in config.
        """
        if installed_pkg in configured_pkgs:
            return True
        
        if "@" in installed_pkg:
            name, installed_version = installed_pkg.split("@", 1)
            # Managed if the base name is in config
            if name in configured_pkgs:
                return True
            
            # Managed if a partial version is in config (e.g., @3.14 matches @3.14.4)
            for configured in configured_pkgs:
                if configured.startswith(f"{name}@") and installed_version.startswith(configured.split("@", 1)[1]):
                    return True
        
        return False
