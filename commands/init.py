"""
ARCHDOTS
help: setup chezmoi and default packages
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

import os
from pathlib import Path
import shutil
import subprocess
import sys
from rich import print
from archdots.ui.console import print_title, prompt, transient_progress
from archdots.core.constants import CHEZMOI_FOLDER, CONFIG_FOLDER, MODULE_PATH
from archdots.core.exceptions import CommandException
from archdots.packages.package import get_packages
from archdots.ui.console import warn_console, confirm
from archdots.packages.dependencies import split_external_dependencies
from archdots.utils import is_url_valid
from shutil import which


# Non-interactive mode detection and helpers
NON_INTERACTIVE = os.environ.get("ARCHDOTS_ASSUME_YES", "0").lower() in ("1", "true", "yes") or not sys.stdin.isatty()


def ask_confirm(message, default=False):
    if NON_INTERACTIVE:
        return default
    return confirm(message, default=default)


def ask_prompt(message, env_var=None):
    if NON_INTERACTIVE:
        if env_var:
            return os.environ.get(env_var, "")
        return ""
    return prompt(message)


def copy_tree_non_destructive(src, dst, overwrite=False):
    src = Path(src)
    dst = Path(dst)
    if not src.exists():
        return
    if not dst.exists():
        shutil.copytree(src, dst, dirs_exist_ok=True)
        return
    for root, dirs, files in os.walk(src):
        rel = Path(root).relative_to(src)
        target_root = dst / rel
        target_root.mkdir(parents=True, exist_ok=True)
        for f in files:
            sfile = Path(root) / f
            tfile = target_root / f
            if tfile.exists() and not overwrite:
                continue
            shutil.copy2(sfile, tfile)


def run_cmd(cmd, cwd=None, check=True, capture_output=False):
    """Run a command and return CompletedProcess. Raise CommandException on failure if check is True."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            shell=False,
            check=check,
            capture_output=capture_output,
            text=True,
            env=None,
        )
        return result
    except subprocess.CalledProcessError as e:
        if check:
            out = e.stdout or ""
            err = e.stderr or ""
            raise CommandException(f"Command {cmd!r} failed. stdout: {out}\nstderr: {err}")
        return e


def git_remotes(cwd):
    """Return a set of remote URLs for a git repo at cwd. Returns empty set if git not available or no remotes."""
    if which("git") is None:
        return set()
    try:
        cp = run_cmd(["git", "remote"], cwd=cwd, check=False, capture_output=True)
        out = cp.stdout or ""
        names = [n.strip() for n in out.splitlines() if n.strip()]
        remotes = set()
        for name in names:
            cp2 = run_cmd(["git", "remote", "get-url", "--all", name], cwd=cwd, check=False, capture_output=True)
            urls = (cp2.stdout or "").splitlines()
            for u in urls:
                if u:
                    remotes.add(u.strip())
        return remotes
    except Exception:
        return set()

with transient_progress("checking packages"):
    default_pkgs = [
        pkg
        for pkg in get_packages(Path(MODULE_PATH) / "default_packages")
        if not pkg.check(supress_output=True)
    ]
    ext_dependencies_by_pm, sorted_packages = split_external_dependencies(
        default_pkgs, default_pkgs
    )
    default_pkgs = sorted_packages

if default_pkgs:
    warn_console.print(
        'This message can be ignored by setting "default_packages: false" on config.yaml'
    )
    print_title("There are unsatisfied dependencies")

    if ask_confirm(
        f'Ready to install: {", ".join(pkg.name for pkg in default_pkgs)}?',
        default=True,
    ):
        failed = []
        for pkg in default_pkgs:
            try:
                pkg.install()
            except Exception as e:
                failed.append((pkg.name, str(e)))
        if failed:
            warn_console.print("Some packages failed to install:")
            for name, err in failed:
                warn_console.print(f" - {name}: {err}")

if os.path.isdir(Path(CHEZMOI_FOLDER) / ".git"):
    print_title(f'chezmoi folder already exists at "{CHEZMOI_FOLDER}"', color="yellow")

CHEZMOI_AVAILABLE = which("chezmoi") is not None
CHEZMOI_PATH = Path(CHEZMOI_FOLDER)

existing_remotes = git_remotes(str(CHEZMOI_PATH))

if CHEZMOI_AVAILABLE:
    if ask_confirm("initialize chezmoi from scratch?", default=True):
        os.makedirs(CHEZMOI_PATH, exist_ok=True)

        GIT_INITIALIZED = (CHEZMOI_PATH / ".git").is_dir()

        # initialize chezmoi and ensure main branch exists when no git yet
        if not GIT_INITIALIZED:
            try:
                run_cmd(["chezmoi", "init"], cwd=str(CHEZMOI_PATH))
            except CommandException:
                warn_console.print("Failed to run 'chezmoi init' — continuing and trying to proceed where possible")

            # try to ensure branch name
            if which("git"):
                try:
                    run_cmd(["git", "-C", str(CHEZMOI_PATH), "branch", "-M", "main"], check=False)
                except Exception:
                    # non-fatal
                    pass

        # copy or create config subfolder (use non-destructive copy)
        cfg_src = Path(CONFIG_FOLDER).expanduser()
        target_config = CHEZMOI_PATH / cfg_src.stem
        if cfg_src.exists() and cfg_src.is_dir():
            copy_tree_non_destructive(cfg_src, target_config, overwrite=False)
        else:
            os.makedirs(target_config, exist_ok=True)
        

        prev_cwd = os.getcwd()
        try:
            os.chdir(str(CHEZMOI_PATH))

            if ask_confirm("use default template?", default=True):
                template_path = Path(MODULE_PATH) / "chezmoi_template"
                copy_tree_non_destructive(template_path, CHEZMOI_PATH, overwrite=False)

            # git add/commit if git is available
            if which("git"):
                try:
                    run_cmd(["git", "add", "."], cwd=str(CHEZMOI_PATH))
                    # commit may fail if there is nothing to commit; try emoji msg then fallback
                    cp = run_cmd(["git", "commit", "-m", ":tada: Init chezmoi"], cwd=str(CHEZMOI_PATH), check=False, capture_output=True)
                    if cp.returncode != 0:
                        # try ASCII fallback
                        run_cmd(["git", "commit", "-m", "Init chezmoi"], cwd=str(CHEZMOI_PATH), check=False)
                except CommandException:
                    warn_console.print("git commit failed — repository may have no changes or git is not fully initialized")

            # if repo already has remotes, don't ask the user
            if existing_remotes:
                warn_console.print(f"git remote(s) already configured: {', '.join(existing_remotes)}")
            else:
                warn_console.print("leave empty to ignore")
                git_origin = ask_prompt("remote git origin", env_var="ARCHDOTS_GIT_ORIGIN")

                if git_origin:
                    if not is_url_valid(git_origin):
                        warn_console.print("The provided URL does not look valid; skipping adding remote.")
                    elif which("git") is None:
                        warn_console.print("git not found; cannot add remote")
                    else:
                        try:
                            run_cmd(["git", "remote", "add", "origin", git_origin], cwd=str(CHEZMOI_PATH))
                            # try pushing; non-fatal if it fails
                            run_cmd(["git", "push", "-u", "origin", "main"], cwd=str(CHEZMOI_PATH), check=False)
                        except CommandException as e:
                            warn_console.print(f"Failed to add or push remote: {e}")

            # apply chezmoi changes
            try:
                run_cmd(["chezmoi", "apply", "-v"], cwd=str(CHEZMOI_PATH), check=False)
            except CommandException:
                warn_console.print("'chezmoi apply' failed — check chezmoi output for details")
        finally:
            os.chdir(prev_cwd)
    elif existing_remotes:
        print_title(f"git remote(s) already configured: {', '.join(existing_remotes)}", color='yellow')
    else:
        git_origin = ask_prompt("remote git origin", env_var="ARCHDOTS_GIT_ORIGIN")
        if not git_origin or not is_url_valid(git_origin):
            raise CommandException("You must specify a valid url")

        try:
            run_cmd(["chezmoi", "init", "--apply", "--verbose", git_origin])
        except CommandException as e:
            raise CommandException(f"chezmoi init failed: {e}")
else:
    warn_console.print("chezmoi not found. If you have already installed it, open a new terminal or refresh the environment variables")


