from pathlib import Path
import json
import os
from dacite.core import from_dict

from archdots.schema import Metadata, ExtendedJSONEncoder
from archdots.exceptions import (
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
        command_tree_json = json.dumps(command_tree, cls=ExtendedJSONEncoder)

        cached_command_tree_path = Path(CACHE_FOLDER) / "command_tree.json"
        cached_metadata_dict_path = Path(CACHE_FOLDER) / "metadata_dict.json"

        cached_metadata_dict = None
        if cached_command_tree_path.is_file() and cached_metadata_dict_path.is_file():
            with open(cached_command_tree_path, "r") as f:
                cached_command_tree = f.read()

            try:
                if command_tree_json == cached_command_tree:
                    with open(cached_metadata_dict_path, "r") as f:
                        cached_metadata_dict = json.load(f)
                    for k, v in cached_metadata_dict.items():

                        cached_metadata_dict[k] = from_dict(Metadata, v)
            except:
                cached_metadata_dict = None

        parser, metadata_dict, parser_dict = build_argparser(
            command_tree, cached_metadata_dict
        )

        args = parser.parse_args()
        run_command(args, metadata_dict, parser_dict)

        os.makedirs(CACHE_FOLDER, exist_ok=True)
        with open(cached_command_tree_path, "w") as f:
            f.write(command_tree_json)
        with open(cached_metadata_dict_path, "w") as f:
            json.dump(metadata_dict, f, cls=ExtendedJSONEncoder)

    except (
        PackageException,
        PackageManagerException,
        ParseException,
        GuiException,
        CommandException,
    ) as e:
        from rich.console import Console

        console = Console(stderr=True, style="bold red", markup=False, highlight=False)

        console.print(e)
        os._exit(1)
    except KeyboardInterrupt:
        pass
