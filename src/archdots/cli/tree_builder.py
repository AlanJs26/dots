import os
from itertools import chain
from pathlib import Path

from archdots.schema import CommandTreeNode


def build_command_tree(roots: list[str], command_name: str):
    excluded_folders = ["__pycache__"]

    root_node = CommandTreeNode(name=command_name, subcommands=[], path=Path(), mtime=0)
    current_node = [root_node]
    for current_folder, dirs, files in chain.from_iterable(
        os.walk(folder, topdown=True) for folder in roots
    ):
        dirs[:] = [dir for dir in dirs if dir not in excluded_folders]

        current_folder = Path(current_folder)
        files = [Path(f) for f in files]

        if str(current_folder) in roots:
            node = root_node
        else:
            node = CommandTreeNode(
                name=current_folder.name,
                subcommands=[],
                path=current_folder,
                mtime=0,
            )

        for file in files:
            filepath = current_folder / file
            node.subcommands.append(
                CommandTreeNode(
                    name=file.stem,
                    subcommands=[],
                    path=filepath,
                    mtime=filepath.stat().st_mtime,
                )
            )

        if node == root_node:
            continue

        node_file = next(filter(lambda f: f.stem == current_folder.name, files), None)

        if node_file:
            node.path = node.path / node_file

        while node.path.parent != current_node[-1].path:
            if current_node[-1] == root_node:
                break
            current_node.pop()

        current_node[-1].subcommands.append(node)
        current_node.append(node)
    return root_node
