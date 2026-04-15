"""
ARCHDOTS
help: sync packages and/or files
arguments:
  - name: type
    required: false
    type: str
    choices: ['pkgs', 'files']
    help: specify type of synching. Leave empty for both
flags:
  - long: --commit
    type: bool
    help: do not re-add files, only do a commit/push
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

import subprocess
import sys
from pathlib import Path

from archdots.core.constants import MODULE_PATH


runner_path = Path(MODULE_PATH) / "runner.py"


def run_archdots(*command_parts: str) -> int:
    command = [sys.executable, str(runner_path), *command_parts]
    return subprocess.run(command, check=False).returncode


requested_type = args["type"]
had_error = False

if not requested_type or requested_type == "pkgs":
    had_error = run_archdots("pkg", "_sync") != 0 or had_error

if not requested_type or requested_type == "files":
    file_args = ["file", "_sync"]
    if args["commit"]:
        file_args.append("--commit")
    had_error = run_archdots(*file_args) != 0 or had_error

exit(1 if had_error else 0)


