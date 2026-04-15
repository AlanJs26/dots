"""
ARCHDOTS
help: run git commands from chezmoi repo
arguments:
  - name: args
    required: true
    type: str
    nargs: "*"
    help: 'custom arguments. To input long flags (i.e. --flag) you must insert "--" at the begining of the arguments. Ex: git -- status --staged'
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

import subprocess


git_args = args["args"] if args["args"] else []
result = subprocess.run(["chezmoi", "git", "--", *git_args], check=False)
exit(result.returncode)
