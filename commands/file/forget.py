"""
ARCHDOTS
help: Remove a target from the source state
arguments:
  - name: files
    required: true
    type: str
    nargs: +
    help: files/folders to forget
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

import os
import subprocess


files = [os.path.expanduser(path) for path in args["files"]]
result = subprocess.run(["chezmoi", "forget", *files], check=False)
exit(result.returncode)

