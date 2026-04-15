import os
import re
from argparse import _SubParsersAction, ArgumentParser
from pathlib import Path
from typing import Optional

from archdots.cli.metadata import extract_metadata
from archdots.schema import Argument, CommandTreeNode, Flag, Metadata

MetadataDict = dict[str, Metadata]
ParserDict = dict[str, tuple[Path, ArgumentParser]]


def parser_from_metadata(name: str, metadata: Metadata, subparser: _SubParsersAction):
    is_hidden = name.startswith("_")
    if is_hidden:
        parser = subparser.add_parser(name)
    else:
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

        name_path = os.sep.join([node.name for node in node_history])
        parent_name_path = os.path.dirname(name_path)

        if next_working_nodes := list(
            filter(lambda n: not n.subcommands and n not in visited_nodes, node.subcommands)
        ):
            pending_nodes.extend(next_working_nodes)

            if parent_name_path not in argparse_dict:
                parser = ArgumentParser(prog=node.name)
            else:
                parser = argparse_dict[parent_name_path]["subparser"].add_parser(
                    node.name, help="+"
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
            filter(lambda n: n.subcommands and n not in visited_nodes, node.subcommands),
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

            argparse_dict[parent_name_path]["subparser"].metavar = (
                "{"
                + ",".join(
                    [
                        parser.prog.split()[-1]
                        for parser in argparse_dict[parent_name_path]["parsers"]
                        if not parser.prog.split()[-1].startswith("_")
                    ]
                )
                + "}"
            )

        visited_nodes.append(node)
        node_history.pop()

    return argparse_dict[command_tree.name]["parser"], metadata_dict, parser_dict
