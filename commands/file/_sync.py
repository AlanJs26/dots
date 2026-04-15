"""
ARCHDOTS
help: sync dotfiles with chezmoi
flags:
    - long: --commit
      type: bool
      help: do not re-add files, only do a commit/push
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

import subprocess
import threading
from rich.progress import Progress, TaskID
from rich.prompt import Confirm, Prompt
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from archdots.config.manager import ConfigManager
from archdots.ui.console import title


def run_command(command: list[str], capture_output=False, text=False) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        check=False,
        capture_output=capture_output,
        text=text,
    )


def commit_changes():
    run_command(["chezmoi", "git", "--", "diff", "--cached", "--stat"])
    if Confirm.ask(title("push changes?"), default=True):
        message = datetime.now().strftime("%d-%m-%y %H:%M:%S")
        if not Confirm.ask(title(f"use default message: {message}?"), default=True):
            while not (message := Prompt.ask(title("new message"))):
                pass
        commit_result = run_command(["chezmoi", "git", "--", "commit", "-m", message])
        if commit_result.returncode != 0:
            return commit_result.returncode

        push_result = run_command(["chezmoi", "git", "--", "push"])
        return push_result.returncode

    return 0


if args["commit"]:
    exit(commit_changes())

commands = {
    "re-add": ["chezmoi", "re-add"],
    "git add": ["chezmoi", "git", "add", "."],
    "chezmoi update": ["chezmoi", "update", "--force", "--apply=false"],
}


def run_and_wait(command: list[str]) -> int:
    try:
        result = run_command(command)
        return result.returncode
    except KeyboardInterrupt:
        from rich import print

        print("[yellow]KeyboardInterrupt")
        return 130


config = ConfigManager().load()
had_error = False


with Progress() as progress:
    task = progress.add_task("Re-adding chezmoi files", total=None)
    had_error = run_and_wait(commands["re-add"]) != 0 or had_error
    progress.update(task, completed=1, total=1)

    failures: list[str] = []
    failures_lock = threading.Lock()

    def chezmoi_forget_thread(task: TaskID, file: str):
        progress.update(task, advance=1, description=f"forgetting {file}")
        returncode = run_and_wait(
            ["chezmoi", "forget", "--force", os.path.expanduser(file)]
        )
        if returncode != 0:
            with failures_lock:
                failures.append(file)

    def chezmoi_add_thread(task: TaskID, file: str):
        progress.update(task, advance=1, description=f"adding {file}")
        returncode = run_and_wait(["chezmoi", "add", "--force", os.path.expanduser(file)])
        if returncode != 0:
            with failures_lock:
                failures.append(file)

    if "chezmoi" in config and isinstance(config["chezmoi"], list):
        task = progress.add_task(
            "forgettting configured chezmoi files", total=len(config["chezmoi"])
        )
        with ThreadPoolExecutor(max_workers=4) as pool:
            for file in config["chezmoi"]:
                pool.submit(chezmoi_forget_thread, task, file)

        task = progress.add_task(
            "adding configured chezmoi files", total=len(config["chezmoi"]) + 1
        )
        # with ThreadPoolExecutor(max_workers=4) as pool:
        for file in config["chezmoi"]:
            progress.update(task, advance=1, description=f"adding {file}")
            returncode = run_and_wait(
                ["chezmoi", "add", "--force", os.path.expanduser(file)]
            )
            if returncode != 0:
                failures.append(file)
            # pool.submit(chezmoi_add_thread, task, file)

    if failures:
        had_error = True

    task = progress.add_task("adding git files", total=None)
    had_error = run_and_wait(commands["git add"]) != 0 or had_error
    progress.update(task, completed=1, total=1)

    # task = progress.add_task("running 'chezmoi update'", total=None)
    # had_error = run_and_wait(commands["chezmoi update"]) != 0 or had_error
    # progress.update(task, completed=1, total=1)

run_command(["chezmoi", "git", "--", "diff", "--cached", "--stat"])

result = run_command(
    ["chezmoi", "git", "--", "diff", "--numstat", "--staged"],
    capture_output=True,
    text=True,
)

stdout = result.stdout

if len(stdout.strip().splitlines()) == 0:
    exit(1 if had_error else 0)

commit_result = commit_changes()
exit(1 if had_error or commit_result != 0 else 0)


