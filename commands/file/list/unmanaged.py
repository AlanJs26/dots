"""
ARCHDOTS
help: shows unmanaged dotfiles
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

from archdots.file_listing import line_paths, print_paths, run_capture


folders = args["folder"] if args["folder"] else []
level = args["level"] if args["level"] else 99

returncode, stdout, stderr = run_capture(["chezmoi", "unmanaged", *folders])
if returncode != 0:
    if stderr:
        print(stderr, end="")
    exit(returncode)

print_paths(line_paths(stdout), use_tree=bool(args["tree"]), level=level)
exit(0)
