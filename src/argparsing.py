import os
import re
import yaml
import importlib.util
from pathlib import Path
from itertools import chain
from typing import NamedTuple, Any
from argparse import _SubParsersAction, ArgumentParser, Namespace, ArgumentError
from src.schema import ArgumentTypeEnum, ParserArgument, ParserConfig


class ParseException(Exception):
    pass


def without_ext(filename) -> str:
    """
    given a path, returns the basename without extension
    """
    return Path(filename).stem


def parser_from_file(filepath, subparser: _SubParsersAction) -> ArgumentParser:
    """
    Receives a filepath and subparser then returns a new parser using the configuration described in file header
    this header is composed of a block delimited by ARCHDOTS, which is written in yaml format
    """
    if os.path.isdir(filepath):
        command_main_script: str | None = next(
            filter(
                lambda x: without_ext(x) == without_ext(filepath), os.listdir(filepath)
            ),
            None,
        )
        if not command_main_script:
            return subparser.add_parser(
                without_ext(filepath), help=f"{without_ext(filepath)} help"
            )
        filepath = os.path.join(filepath, command_main_script)

    with open(filepath, "r") as f:
        content = f.read()

    match = next(
        map(
            lambda x: x.strip(),
            re.findall(r"ARCHDOTS(.+)ARCHDOTS", content, flags=re.DOTALL),
        ),
        None,
    )

    if not match:
        return subparser.add_parser(
            without_ext(filepath), help=f"{without_ext(filepath)} help"
        )

    parsed_config = ParserConfig(**yaml.safe_load(match))

    parser = subparser.add_parser(without_ext(filepath), help=parsed_config.help)

    for argument in [*parsed_config.arguments, *parsed_config.flags]:
        match argument.type:
            case ArgumentTypeEnum.bool:
                extra_args = {"action": "store_true"}
            case ArgumentTypeEnum.int:
                extra_args = {"action": "store", "type": int, "nargs": argument.nargs}
            case ArgumentTypeEnum.str | _:
                extra_args = {"action": "store", "type": str, "nargs": argument.nargs}

        if isinstance(argument, ParserArgument):
            names = [argument.name]
        else:
            names = [argument.long]
            if "short" in argument:
                names.append(argument.short)
        parser.add_argument(*filter(str, names), help=argument.help, **extra_args)

    return parser


class Depth(NamedTuple):
    subparser: _SubParsersAction
    parser: ArgumentParser
    path: str


def parse_folder(
    folders: list[str], command_folder="commands"
) -> tuple[ArgumentParser, dict[int, list[Depth]]]:
    """
    walks through all subfolders of all `folders` and setup and cli parser based on filestructure
    """
    # create the top-level parser
    parser = ArgumentParser(prog="archdots")

    folders = [os.path.join(folder, command_folder) for folder in folders]

    depths = {
        0: [Depth(parser.add_subparsers(dest=command_folder), parser, command_folder)]
    }

    for current_folder, dirs, files in chain.from_iterable(
        os.walk(folder, topdown=True) for folder in folders
    ):
        current_folder_without_prefix = current_folder
        for folder in sorted(folders, key=len, reverse=True):
            if current_folder.startswith(folder):
                current_folder_without_prefix = current_folder.replace(folder, "", 1)
                break

        current_root = os.path.normpath(current_folder_without_prefix).split(os.sep)[1:]

        if current_root and current_root[-1].startswith("_"):
            continue

        if len(current_root) == 0:
            # root
            current_depths = depths[0]
        elif len(files) == 1 and without_ext(files[0]) == current_root[-1]:
            # folder with only a file with the same name
            current_depths = depths[len(current_root) - 1]
            previous_depth = depths[len(current_root) - 1][-1]

            new_parser = parser_from_file(current_folder, previous_depth.subparser)
        elif len(current_root) >= len(depths) or (
            current_root and current_folder != depths[len(current_root)][-1].path
        ):
            # entering new folder
            if not len(current_root) in depths:
                depths[len(current_root)] = []
            current_depths = depths[len(current_root)]

            previous_depth = depths[len(current_root) - 1][-1]

            try:
                new_parser = parser_from_file(current_folder, previous_depth.subparser)
            except ArgumentError as e:
                if current_root[-1] == command_folder:
                    continue
                raise e

            new_sub_parser = new_parser.add_subparsers(dest=current_root[-1])
            current_depths.append(Depth(new_sub_parser, new_parser, current_folder))

        else:
            # fallback. Will never happen, but lsp bother if left without it
            current_depths = depths[len(current_root)]

        for file in files:
            # single file commands
            command_name = without_ext(file)
            if current_root and command_name == current_root[-1]:
                continue
            if file.startswith("_"):
                continue

            new_parser = parser_from_file(
                os.path.join(current_folder, file), current_depths[-1].subparser
            )
    return (parser, depths)


def run_command(
    args: Namespace,
    root_basename: str,
    roots: list[str],
    depths: dict[int, list[Depth]],
):
    """
    find correct command based on argparse result

    `args` argparse result
    `root_basename` name of the folder containing rules
    `roots` path of all folders to search for commands
    `depths` dictionary returned from `parse_folder` that contains all subparsers for each command
    """
    path = root_basename
    args_dict: dict[str, Any] = vars(args)
    # extract command path and arguments from argparse Namespace
    while (current_command := os.path.basename(path)) in args_dict:
        if not args_dict[current_command]:
            break

        path = os.path.join(path, args_dict[current_command])
        del args_dict[current_command]

    # check which root that contains the command
    for root in sorted(roots, key=len, reverse=True):
        abs_path = Path(root) / path
        if os.path.exists(abs_path) or (
            Path(abs_path).parent.exists()
            and next(
                filter(
                    lambda x: without_ext(x) == without_ext(path),
                    os.listdir(Path(abs_path).parent),
                ),
                None,
            )
        ):
            path = abs_path
            break

    # the path to a command can be a folder or a file.
    parent = path
    if not os.path.isdir(path):
        parent = Path(path).parent

    # Search for a file inside parent that has the same basename as path
    command_main_script: str | None = next(
        filter(lambda x: without_ext(x) == without_ext(path), os.listdir(parent)), None
    )

    if not command_main_script:
        splited_path = os.path.normpath(path).split(os.sep)[1:]
        # find the subparser associated with path
        subparser = next(
            filter(lambda d: Path(d.path) == Path(path), depths[len(splited_path)]),
            None,
        )

        # This should never happen.
        if not subparser:
            raise Exception(
                "This command does not exist or there is some error on command parsing"
            )
        # if reached this point, means that typed command there is no entry point, only contains subcomands.
        # show help
        subparser.parser.print_help()
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

    fullpath = os.path.join(parent, command_main_script)

    if command_main_script.endswith(".py"):
        # import python file and create a global variable named "args" that contains all passed arguments to the command
        spec = importlib.util.spec_from_file_location(os.path.basename(path), fullpath)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            module.__dict__["args"] = args_dict
            spec.loader.exec_module(module)
        pass
    else:
        # convert all arguments into variable
        bashdict = ""
        for key, value in args_dict.items():
            bashdict += f'["{key}"]={parse_value(value)} '
        bashdict = "declare -A args=(" + bashdict.strip() + ")"

        if command_main_script.endswith("sh"):
            command = f"{bashdict}\nsource {fullpath}"
        else:
            command = f"{bashdict}\n./{fullpath.replace(' ', '\\ ')}"

        os.system(command)
