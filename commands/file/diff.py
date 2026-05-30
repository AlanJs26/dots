"""
ARCHDOTS
help: show diff since last dotfiles sync
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

import subprocess


reverse_diff = subprocess.run(
    ["chezmoi", "diff", "--reverse"],
    check=False,
    capture_output=True,
    text=True,
)

if reverse_diff.returncode != 0:
    if reverse_diff.stderr:
        print(reverse_diff.stderr, end="")
    exit(reverse_diff.returncode)

if reverse_diff.stdout.strip():
    print(reverse_diff.stdout, end="")
    exit(0)

fallback = subprocess.run(["chezmoi", "git", "--", "diff", "--cached"], check=False)
exit(fallback.returncode)


