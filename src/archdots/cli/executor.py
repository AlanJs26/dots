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
        if not args_dict[current_command]:
            break

        path = os.path.join(path, args_dict[current_command])
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
