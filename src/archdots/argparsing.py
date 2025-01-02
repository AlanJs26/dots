import os
import re
from dacite import from_dict
from dacite.exceptions import WrongTypeError
import yaml

from pathlib import Path
from itertools import chain
from typing import Any, Optional
from argparse import _SubParsersAction, ArgumentParser, Namespace

from archdots.exceptions import ParseException
from archdots.schema import (
    Argument,
    Metadata,
    CommandTreeNode,
    Flag,
    Argument,
)

MetadataDict = dict[str, Metadata]
ParserDict = dict[str, tuple[Path, ArgumentParser]]


def parser_from_metadata(name: str, metadata: Metadata, subparser: _SubParsersAction):
    parser = subparser.add_parser(name, help=metadata.help)

    argument: Flag | Argument
    for argument in [*metadata.arguments, *metadata.flags]:
        match argument.type:
            case "bool":
                extra_args = {"action": "store_true"}
            case "int":
                extra_args = {"action": "store", "type": int, "nargs": argument.nargs}
            case "str" | _:
                extra_args = {"action": "store", "type": str, "nargs": argument.nargs}

        if argument.choices:
            extra_args = {
                "action": "store",
                "type": str,
                "nargs": argument.nargs,
                "choices": argument.choices,
            }

        if isinstance(argument, Argument):
            names = [argument.name]
            if not argument.required and argument.nargs != "*":
                extra_args["nargs"] = "?"
        else:
            long_name = "--" + re.sub("^--", "", argument.long)
            names = [long_name]
            if argument.short:
                short_name = "-" + re.sub("^-", "", argument.short)
                names.append(short_name)
        parser.add_argument(*filter(str, names), help=argument.help, **extra_args)

    return parser


def extract_metadata(filepath: str | Path):
    filepath = Path(filepath)
    if filepath.is_dir():
        return Metadata(help=f"{filepath.stem} help")

    with open(filepath, "r") as f:
        content = f.read()

    match = next(
        map(
            lambda x: x.strip(),
            re.findall(r"ARCHDOTS(.+?)ARCHDOTS", content, flags=re.DOTALL),
        ),
        None,
    )

    if not match:
        return Metadata(help=f"{filepath.stem} help")

    try:
        return from_dict(Metadata, yaml.safe_load(match))
    except WrongTypeError as e:
        raise ParseException(str(e), str(filepath))


def build_argparser(
    command_tree: CommandTreeNode,
    metadata_dict: Optional[MetadataDict] = None,
) -> tuple[ArgumentParser, MetadataDict, ParserDict]:
    argparse_dict = {}
    parser_dict = {}
    if not metadata_dict:
        metadata_dict = {}

    pending_nodes = [command_tree]
    visited_nodes: list[CommandTreeNode] = []
    node_history: list[CommandTreeNode] = []

    while pending_nodes:
        node = pending_nodes[-1]
        if node not in node_history:
            node_history.append(node)

        name_path = "/".join([node.name for node in node_history])
        parent_name_path = os.path.dirname(name_path)

        if next_working_nodes := list(
            filter(
                lambda n: not n.subcommands and n not in visited_nodes, node.subcommands
            )
        ):
            pending_nodes.extend(next_working_nodes)

            if parent_name_path not in argparse_dict:
                parser = ArgumentParser(prog=node.name)
            else:
                parser = argparse_dict[parent_name_path]["subparser"].add_parser(
                    node.name, help=node.name
                )

            subparser = parser.add_subparsers(dest=node.name)

            argparse_dict[name_path] = {
                "parser": parser,
                "subparser": subparser,
                "parsers": [],
            }
            parser_dict[name_path] = (node.path, parser)
            if name_path not in metadata_dict:
                metadata_dict[name_path] = extract_metadata(node.path)

            continue

        if next_node := next(
            filter(
                lambda n: n.subcommands and n not in visited_nodes, node.subcommands
            ),
            None,
        ):
            pending_nodes.append(next_node)
            continue
        else:
            pending_nodes.pop()

        if not node.subcommands:
            if name_path not in metadata_dict:
                metadata_dict[name_path] = extract_metadata(node.path)

            parser = parser_from_metadata(
                node.name,
                metadata_dict[name_path],
                argparse_dict[parent_name_path]["subparser"],
            )

            parser_dict[name_path] = (node.path, parser)
            argparse_dict[parent_name_path]["parsers"].append(parser)

        visited_nodes.append(node)
        node_history.pop()

    return argparse_dict[command_tree.name]["parser"], metadata_dict, parser_dict


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

        node_file = next(
            filter(lambda f: f.stem == current_folder.name, files), None  # type: ignore
        )

        if node_file:
            node.path = node.path / node_file

        while node.path.parent != current_node[-1].path:
            if current_node[-1] == root_node:
                break
            current_node.pop()

        current_node[-1].subcommands.append(node)
        current_node.append(node)
    return root_node


def run_command(args: Namespace, metadata_dict: MetadataDict, parser_dict: ParserDict):
    path = next(key for key in metadata_dict.keys())

    args_dict: dict[str, Any] = vars(args)
    # extract command path and arguments from argparse Namespace
    while (current_command := os.path.basename(path)) in args_dict:
        if not args_dict[current_command]:
            break

        path = os.path.join(path, args_dict[current_command])
        del args_dict[current_command]

    script_path, parser = parser_dict[path]

    if script_path.is_dir():
        parser.print_help()
        return

    def parse_value(value, no_quotes=False):
        quotes = lambda x: x if no_quotes else '"' + x + '"'

        if isinstance(value, bool):
            return int(value)
        if value is None:
            return quotes("")
        if isinstance(value, list):
            return quotes(
                " ".join(map(lambda x: str(parse_value(x, no_quotes=True)), value))
            )
        else:
            return quotes(value)

    if str(script_path).endswith(".py"):
        import importlib.util

        # import python file and create a global variable named "args" that contains all passed arguments to the command
        spec = importlib.util.spec_from_file_location(
            os.path.basename(path), str(script_path)
        )
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            module.__dict__["args"] = args_dict
            spec.loader.exec_module(module)
    else:
        # convert all arguments into variable
        bashdict = ""
        for key, value in args_dict.items():
            bashdict += f'["{key}"]={parse_value(value)} '
        bashdict = "declare -A args=(" + bashdict.strip() + ")"

        command = 'ARCHDOTS="python runner.py"\n'

        if str(script_path).endswith("sh"):
            command += f"{bashdict}\nsource {str(script_path)}"
        else:
            command += f"{bashdict}\n./{str(script_path).replace(' ', '\\ ')}"

        os.system(command)
