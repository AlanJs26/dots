import os
import subprocess
from pathlib import Path
from shutil import which

from archdots.core.constants import PLATFORM
from archdots.ui.console import print_title
from archdots.core.exceptions import PackageException

PWSH_AVAILABLE = which("pwsh") is not None


def run_pkgbuild_function(package, name: str, supress_output=False, sources: list[str] | None = None) -> int:
    """Execute one function from a package PKGBUILD script."""
    sources = sources or []
    os.makedirs(package.get_cache_folder(), exist_ok=True)

    if PLATFORM == "linux":
        bashdict = ""
        if sources:
            for i, folder in enumerate(sources):
                bashdict += f'["{i}"]="{folder}" '
            bashdict = "declare -A sourced=(" + bashdict.strip() + ")"

        command = f"""
        PKGPATH=\"{os.path.dirname(package.pkgbuild)}\"
        {bashdict}
        source {os.path.abspath(package.pkgbuild)}
        {name}
        """

        process = subprocess.Popen(
            command,
            shell=True,
            executable=None,
            stdout=subprocess.DEVNULL if supress_output else None,
            stderr=subprocess.DEVNULL if supress_output else None,
            cwd=package.get_cache_folder(),
        )
    else:
        hashtable = ""
        if sources:
            hashtable = "$sourced = @{\n"
            for i, folder in enumerate(sources):
                hashtable += f'"{i}" = "{folder}"\n'
            hashtable += "}"

        from archdots.package_parser import Function, PackageTransformer, parser

        with open(package.pkgbuild, "r") as f:
            text = f.read()
        tree = parser.parse(text)
        parsed_functions: list[Function] = [
            fn for fn in PackageTransformer().transform(tree) if isinstance(fn, Function)
        ]

        found_function = next(filter(lambda item: item.name == name, parsed_functions), None)
        if not found_function:
            raise PackageException(
                f'tried to executed an unknown PKGBUILD function "{found_function}"',
                package,
            )

        file_command_path = Path(package.get_cache_folder()) / f"{name}.ps1"
        with open(file_command_path, "w") as f:
            f.write(
                '$ErrorActionPreference = "Stop"\n'
                + r"""
                   function Uninstall-Program {Param([string]$name)
                   $uninstall32 = gci "HKLM:\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall" | foreach { gp $_.PSPath } | ? { $_ -match $name } | select UninstallString
                   $uninstall64 = gci "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall" | foreach { gp $_.PSPath } | ? { $_ -match $name } | select UninstallString

                   if ($uninstall64) {
                   $uninstall64 = $uninstall64.UninstallString -Replace "msiexec.exe","" -Replace "/I","" -Replace "/X",""
                   $uninstall64 = $uninstall64.Trim()
                   Write "Uninstalling..."
                   start-process "msiexec.exe" -arg "/X $uninstall64 /qb" -Wait}
                   if ($uninstall32) {
                   $uninstall32 = $uninstall32.UninstallString -Replace "msiexec.exe","" -Replace "/I","" -Replace "/X",""
                   $uninstall32 = $uninstall32.Trim()
                   Write "Uninstalling..."
                   start-process "msiexec.exe" -arg "/X $uninstall32 /qb" -Wait}
                   }
                   """
                + "function which {Param([string]$command) if ((Get-Command $command -ErrorAction SilentlyContinue) -eq $null) {exit 1}}"
                + '$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")\n'
                + '[System.Environment]::SetEnvironmentVariable("Path", $env:Path, "Process")\n'
                + 'if ((Get-Command refreshenv -ErrorAction SilentlyContinue) -ne $null) {refreshenv}\n'
                + f'$PKGPATH = "{os.path.dirname(package.pkgbuild)}"\n{hashtable}\n{found_function.content}'
            )

        powershell_cmd = "pwsh" if PWSH_AVAILABLE else "powershell"
        command = f"{powershell_cmd} -ExecutionPolicy ByPass -File {file_command_path.resolve()}"

        process = subprocess.Popen(
            ["cmd", "/c", command],
            stdout=subprocess.DEVNULL if supress_output else None,
            stderr=subprocess.DEVNULL if supress_output else None,
            cwd=package.get_cache_folder(),
        )

    process.communicate()
    return int(process.returncode)


def check(package, supress_output=False):
    if not supress_output:
        print_title("Checking")

    if package.source_on_check:
        sources = package.fetch_sources()
        os.makedirs(package.get_cache_folder(), exist_ok=True)
        with open(Path(package.get_cache_folder()) / "sources.txt", "w") as f:
            f.writelines(sources)
    else:
        sources = []

    return run_pkgbuild_function(package, "check", supress_output, sources) == 0


def update(package, supress_output=False, force=False):
    if not supress_output:
        print_title(f"Updating [cyan]{package.name}")
    if not force and package.check(supress_output) and "install" not in package.available_functions:
        print_title(f"{package.name} Already installed", color="yellow")
        return

    sources = package.fetch_sources()
    with open(Path(package.get_cache_folder()) / "sources.txt", "w") as f:
        f.writelines(sources)

    status = run_pkgbuild_function(package, "update", supress_output, sources) == 0
    if status:
        print_title(f"Successfully updated [cyan]{package.name}", color="green")
    return status


def install(package, supress_output=False, force=False):
    if not supress_output:
        print_title(f"Installing [cyan]{package.name}")
    if not force and package.check(supress_output):
        print_title(f"{package.name} Already installed", color="yellow")
        return

    sources = package.fetch_sources()
    with open(Path(package.get_cache_folder()) / "sources.txt", "w") as f:
        f.writelines(sources)

    status = run_pkgbuild_function(package, "install", supress_output, sources) == 0
    if status:
        print_title(f"Successfully installed [cyan]{package.name}", color="green")
    return status


def uninstall(package, supress_output=False, force=False):
    if not supress_output:
        print_title(f"Uninstalling [cyan]{package.name}")

    if not force and not package.check(supress_output):
        print_title(f"{package.name} is not installed. Cannot uninstall", color="red")
        return

    sources_txt = Path(package.get_cache_folder()) / "sources.txt"
    sources: list[str] = []
    if os.path.isfile(sources_txt):
        with open(sources_txt, "r") as f:
            sources = [line.strip() for line in f.readlines()]

    status = run_pkgbuild_function(package, "uninstall", supress_output, sources) == 0
    if status:
        print_title(f"Successfully uninstalled [cyan]{package.name}", color="green")
    return status
