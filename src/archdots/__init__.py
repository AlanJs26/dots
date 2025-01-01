from pathlib import Path
import json
import os

from pydantic import ValidationError

from archdots.schema import ParserConfig, ExtendedJSONEncoder
from archdots.utils import (
    CommandException,
    GuiException,
    PackageManagerException,
    PackageException,
    ParseException,
)
from archdots.constants import (
    CONFIG_FOLDER,
    COMMANDS_FOLDER,
    MODULE_PATH,
    CACHE_FOLDER,
)
from archdots.argparsing import (
    run_command,
    build_command_tree,
    build_argparser,
)


def main():
    """
    archdots entrypoint
    """
    try:
        roots = [
            str(Path(p) / Path(COMMANDS_FOLDER).name)
            for p in (MODULE_PATH, CONFIG_FOLDER)
        ]
        command_tree = build_command_tree(roots, "archdots")

        cached_command_tree_path = Path(CACHE_FOLDER) / "command_tree.json"
        cached_metadata_dict_path = Path(CACHE_FOLDER) / "metadata_dict.json"

        cached_metadata_dict = None
        if cached_command_tree_path.is_file() and cached_metadata_dict_path.is_file():
            with open(cached_command_tree_path, "r") as f:
                cached_command_tree = f.read()

            if command_tree.model_dump_json() == cached_command_tree:
                with open(cached_metadata_dict_path, "r") as f:
                    cached_metadata_dict = json.load(f)
                for k, v in cached_metadata_dict.items():
                    cached_metadata_dict[k] = ParserConfig.model_validate_json(v)

        parser, metadata_dict, parser_dict = build_argparser(
            command_tree, cached_metadata_dict
        )

        args = parser.parse_args()
        run_command(args, metadata_dict, parser_dict)

        with open(cached_command_tree_path, "w") as f:
            f.write(command_tree.model_dump_json())
        with open(cached_metadata_dict_path, "w") as f:
            json.dump(metadata_dict, f, cls=ExtendedJSONEncoder)

    except (
        PackageException,
        PackageManagerException,
        ParseException,
        ValidationError,
        GuiException,
        CommandException,
    ) as e:
        from rich.console import Console

        console = Console()

        console.print(e, style="red")
        os._exit(1)
    except KeyboardInterrupt:
        pass
