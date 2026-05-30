import importlib.util
import os
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Any

from archdots.core.constants import MODULE_PATH
from archdots.schema import Metadata

MetadataDict = dict[str, Metadata]
ParserDict = dict[str, tuple[Path, ArgumentParser]]


def run_command(args: Namespace, metadata_dict: MetadataDict, parser_dict: ParserDict):
    path = next(key for key in metadata_dict.keys())

    args_dict: dict[str, Any] = vars(args)
    while (current_command := os.path.basename(path)) in args_dict:
        subcommand = args_dict[current_command]
        if not subcommand or isinstance(subcommand, list):
            break
        
        # Check if the next part in the path exists before committing to it.
        # This prevents including positional arguments in the path.
        next_path = os.path.join(path, subcommand)
        if next_path not in metadata_dict and next_path not in parser_dict:
            break

        path = next_path
        del args_dict[current_command]

    script_path, parser = parser_dict[path]

    if script_path.is_dir():
        parser.print_help()
        return

    def parse_value(value, no_quotes=False):
        quotes = lambda x: x if no_quotes else f'"{x}"'

        if isinstance(value, bool):
            return int(value)
        if value is None:
            return quotes("")
        if isinstance(value, list):
            return quotes(" ".join(map(lambda x: str(parse_value(x, no_quotes=True)), value)))
        return quotes(value)

    if str(script_path).endswith(".py"):
        spec = importlib.util.spec_from_file_location(os.path.basename(path), str(script_path))
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            module.__dict__["args"] = args_dict
            spec.loader.exec_module(module)
    else:
        bashdict = ""
        for key, value in args_dict.items():
            bashdict += f'["{key}"]={parse_value(value)} '
        bashdict = "declare -A args=(" + bashdict.strip() + ")"

        command = f'ARCHDOTS="python {os.path.join(MODULE_PATH, "runner.py")}"\n'

        if str(script_path).endswith("sh"):
            command += f"{bashdict}\nsource {str(script_path)}"
        else:
            command += f"{bashdict}\n./{str(script_path).replace(' ', '\\ ')}"

        os.system(command)
