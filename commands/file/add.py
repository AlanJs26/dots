"""
ARCHDOTS
help: adds files to chezmoi
arguments:
  - name: target_files
    required: true
    type: str
    nargs: +
    help: files to add
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

import os
import subprocess


target_files = [os.path.expanduser(path) for path in args["target_files"]]
result = subprocess.run(["chezmoi", "add", *target_files], check=False)
exit(result.returncode)