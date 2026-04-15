"""
ARCHDOTS
help: shows pending dotfiles
arguments:
  - name: folder
    required: false
    type: str
    nargs: "*"
    help: folders
flags:
  - long: --level
    type: int
    help: sets tree view max depth level
  - long: --tree
    type: bool
    help: display folders as a tree
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

import re

from archdots.ui.path_display import normalize_display_path, print_paths, run_capture


def parse_git_cached_files(stdout: str) -> list[str]:
    paths: list[str] = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split(maxsplit=2)
        if len(parts) < 3:
            continue
        parsed = parts[2].replace("dot_", ".")
        parsed = parsed.replace("private_", "")
        parsed = parsed.replace("executable_", "")
        paths.append(parsed)
    return paths


def parse_chezmoi_diff_files(stdout: str) -> list[str]:
    matches = re.findall(r"^diff --git a/(.+?) b/.+$", stdout, flags=re.MULTILINE)
    return matches


def filter_by_folders(paths: list[str], folders: list[str]) -> list[str]:
    if not folders:
        return paths

    normalized_folders = [normalize_display_path(folder) for folder in folders]
    filtered: list[str] = []
    for path in paths:
        display_path = normalize_display_path(path)
        if any(
            display_path == folder or display_path.startswith(folder.rstrip("/") + "/")
            for folder in normalized_folders
        ):
            filtered.append(path)
    return filtered


folders = args["folder"] if args["folder"] else []
level = args["level"] if args["level"] else 99

cached_code, cached_stdout, cached_stderr = run_capture(
    ["chezmoi", "git", "--", "diff", "--cached", "--numstat"]
)
if cached_code != 0:
    if cached_stderr:
        print(cached_stderr, end="")
    exit(cached_code)

diff_code, diff_stdout, diff_stderr = run_capture(["chezmoi", "diff"])
if diff_code != 0:
    if diff_stderr:
        print(diff_stderr, end="")
    exit(diff_code)

pending = parse_git_cached_files(cached_stdout) + parse_chezmoi_diff_files(diff_stdout)
pending = sorted({normalize_display_path(path) for path in pending})
pending = sorted({normalize_display_path(path) for path in filter_by_folders(pending, folders)})

print_paths(pending, use_tree=bool(args["tree"]), level=level)
exit(0)


