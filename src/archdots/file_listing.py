from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
import subprocess

from rich import print
from rich.tree import Tree


def run_capture(command: list[str]) -> tuple[int, str, str]:
    process = subprocess.run(command, check=False, capture_output=True, text=True)
    return process.returncode, process.stdout, process.stderr


def line_paths(stdout: str) -> list[str]:
    return [line.strip() for line in stdout.splitlines() if line.strip()]


def print_paths(paths: Iterable[str], use_tree: bool, level: int) -> None:
    normalized = sorted({normalize_display_path(path) for path in paths if path.strip()})
    if not normalized:
        return

    if not use_tree:
        print("\n".join(normalized))
        return

    tree = Tree("~")
    hierarchy: dict[str, dict] = lambda_dict()
    for path in normalized:
        rel = path[2:] if path.startswith("~/") else path
        parts = [chunk for chunk in rel.split("/") if chunk]
        if not parts:
            continue
        for idx, chunk in enumerate(parts):
            if idx + 1 > level:
                break
            hierarchy = insert_chunk(hierarchy, parts[: idx + 1])

    render_hierarchy(tree, hierarchy)
    print(tree)


def normalize_display_path(path: str) -> str:
    fixed = path.strip().replace("\\", "/")
    if fixed.startswith("~/"):
        return fixed
    if fixed.startswith("/"):
        return f"~{fixed}"
    return f"~/{fixed.lstrip('./')}"


def lambda_dict() -> dict[str, dict]:
    return defaultdict(lambda: defaultdict(dict))


def insert_chunk(tree: dict[str, dict], chunks: list[str]) -> dict[str, dict]:
    current = tree
    for chunk in chunks:
        if chunk not in current:
            current[chunk] = {}
        current = current[chunk]
    return tree


def render_hierarchy(parent: Tree, hierarchy: dict[str, dict]) -> None:
    for name in sorted(hierarchy):
        child = parent.add(name)
        if hierarchy[name]:
            render_hierarchy(child, hierarchy[name])
