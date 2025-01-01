"""
ARCHDOTS
help: sync dotfiles with chezmoi
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

import subprocess
from rich.progress import Progress, TaskID
from rich.prompt import Confirm, Prompt
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from archdots.settings import read_config

commands = {
    "re-add": "chezmoi re-add",
    "git add": "chezmoi git add .",
    "chezmoi update": "chezmoi update --force",
}


def run_and_wait(command: str) -> int:
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
        shell=True,
    )
    return process.wait()


config = read_config()


with Progress() as progress:
    task = progress.add_task("adding git files", total=None)
    run_and_wait(commands["git add"])
    progress.update(task, completed=1, total=1)

    def chezmoi_add_thread(task: TaskID, file: str):
        run_and_wait(f'chezmoi add "{os.path.expanduser(file)}"')
        progress.update(task, advance=1, description=file)

    if "chezmoi" in config and isinstance(config["chezmoi"], list):
        task = progress.add_task("adding git files", total=len(config["chezmoi"]))
        with ThreadPoolExecutor(max_workers=4) as pool:
            for file in config["chezmoi"]:
                pool.submit(chezmoi_add_thread, task, file)

    task = progress.add_task("Re-adding", total=None)
    run_and_wait(commands["re-add"])
    progress.update(task, completed=1, total=1)

    task = progress.add_task("running 'chezmoi update'", total=None)
    run_and_wait(commands["chezmoi update"])
    progress.update(task, completed=1, total=1)

    task = progress.add_task("adding git files", total=None)
    run_and_wait(commands["git add"])
    progress.update(task, completed=1, total=1)

os.system("chezmoi git -- diff --cached --stat")

process = subprocess.Popen(
    "chezmoi git -- diff --numstat --staged",
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    stdin=subprocess.PIPE,
    shell=True,
    text=True,
)

stdout, stderr = process.communicate()

if len(stdout.strip().splitlines()) == 0:
    exit()

if Confirm.ask("[cyan]:: [/]push changes?", default=True):
    message = datetime.now().strftime("%d-%m-%y %H:%M:%S")
    if not Confirm.ask(f"[cyan]:: [/]use default message: {message}?", default=True):
        while not (message := Prompt.ask("[cyan]:: [/]new message")):
            pass
    os.system(f'chezmoi git -- commit -m "{message}"')
    os.system(f"chezmoi git push")
