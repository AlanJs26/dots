import os
import subprocess
from pathlib import Path
from shutil import which

from archdots.ui.console import print_title, warn_console
from archdots.core.exceptions import PackageException
from archdots.core.platforms.registry import get_current_platform

current_platform = get_current_platform()

if current_platform.supports("windows"):
    _git_sh = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git" / "bin" / "sh.exe"
    if _git_sh.exists():
        BASH_CMD = f'"{_git_sh}"'
    else:
        _bash = which("bash") or which("sh")
        if _bash:
            BASH_CMD = f'"{_bash}"'
        else:
            warn_console.print("No valid bash/sh shell found (looked in Program Files/Git/bin and PATH). Execution may fail.")
            BASH_CMD = "sh"
else:
    BASH_CMD = "bash"


def run_pkgbuild_function(package, name: str, supress_output=False, sources: list[str] | None = None) -> int:
    """Execute one function from a package PKGBUILD script."""
    sources = sources or []
    os.makedirs(package.get_cache_folder(), exist_ok=True)
    sudo = 'gsudo' if get_current_platform().supports("windows") else 'sudo'

    from archdots.package_parser import parse_from_path
    _, parsed_functions = parse_from_path(package.pkgbuild)
    
    found_function = next(filter(lambda func: func.name in (name, f"{name}_powershell"), parsed_functions), None)
    if not found_function:
        raise PackageException(
            f'tried to executed an unknown PKGBUILD function "{name}"',
            package,
        )

    if found_function.name.endswith("_powershell"):
        hashtable = ""
        if sources:
            hashtable = "$sourced = @{\n"
            for i, folder in enumerate(sources):
                hashtable += f'"{i}" = "{folder}"\n'
            hashtable += "}"

        file_command_path = Path(package.get_cache_folder()) / f"{name}.ps1"
        with open(file_command_path, "w", encoding="utf-8") as f:
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
                + f'$PKGPATH = "{os.path.dirname(package.pkgbuild)}"\n{hashtable}\n{found_function.content}'
            )

        powershell_cmd = which("pwsh") or which("powershell")
        if not powershell_cmd:
            warn_console.print("PowerShell (pwsh or powershell) not found. Execution may fail.")
            powershell_cmd = "pwsh"
        command = f"{sudo if package.elevated else ''} \"{powershell_cmd}\" -ExecutionPolicy ByPass -File \"{file_command_path.resolve()}\"".strip()

        process = subprocess.Popen(
            command,
            shell=True,
            executable=None,
            stdout=subprocess.DEVNULL if supress_output else None,
            stderr=subprocess.DEVNULL if supress_output else None,
            cwd=package.get_cache_folder(),
        )
    else:
        bashdict = ""
        if sources:
            for i, folder in enumerate(sources):
                bashdict += f'["{i}"]="{folder}" '
            bashdict = "declare -A sourced=(" + bashdict.strip() + ")"

        file_command_path = Path(package.get_cache_folder()) / f"{name}.sh"
        with open(file_command_path, "w", encoding="utf-8") as f:
            # We fix line endings avoiding windows \r\n issues on bash
            content = found_function.content.replace('\r\n', '\n')
            f.write(f'PKGPATH="{os.path.dirname(package.pkgbuild).replace(os.sep, "/")}"\n{bashdict}\n\n{content}\n')

        command = f"{sudo if package.elevated else ''} {BASH_CMD} \"{file_command_path.resolve()}\"".strip()

        process = subprocess.Popen(
            command,
            shell=True,
            executable=None,
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
        with open(Path(package.get_cache_folder()) / "sources.txt", "w", encoding="utf-8") as f:
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
    with open(Path(package.get_cache_folder()) / "sources.txt", "w", encoding="utf-8") as f:
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
    with open(Path(package.get_cache_folder()) / "sources.txt", "w", encoding="utf-8") as f:
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
        with open(sources_txt, "r", encoding="utf-8") as f:
            sources = [line.strip() for line in f.readlines()]

    status = run_pkgbuild_function(package, "uninstall", supress_output, sources) == 0
    if status:
        print_title(f"Successfully uninstalled [cyan]{package.name}", color="green")
    return status
