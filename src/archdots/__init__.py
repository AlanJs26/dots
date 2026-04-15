from pathlib import Path
import json
import os
from shutil import which

from archdots.schema import ExtendedJSONEncoder
from archdots.cli.cache import load_cached_metadata, save_parser_cache
from archdots.core.exceptions import (
    CommandException,
    GuiException,
    PackageManagerException,
    PackageException,
    ParseException,
    SettingsException,
)
from archdots.core.constants import (
    CHEZMOI_FOLDER,
    CONFIG_FOLDER,
    COMMANDS_FOLDER,
    MODULE_PATH,
    CACHE_FOLDER,
    PLATFORM,
)
from archdots.cli.runner import (
    run_command,
    build_command_tree,
    build_argparser,
)


def main():
    """
    archdots entrypoint
    """

    if which("chezmoi") is None:
        from archdots.ui.console import warn_console

        warn_console.print(
            'chezmoi is not installed. Run "dots init" to install it and setup your repository'
        )

    try:
        roots = [
            str(Path(p) / Path(COMMANDS_FOLDER).name)
            for p in (MODULE_PATH, CONFIG_FOLDER)
        ]
        command_tree = build_command_tree(roots, "archdots")
        command_tree_json = json.dumps(command_tree, cls=ExtendedJSONEncoder)

        cached_metadata_dict = load_cached_metadata(CACHE_FOLDER, command_tree_json)

        parser, metadata_dict, parser_dict = build_argparser(
            command_tree, cached_metadata_dict
        )
        parser.add_argument("--info", action="store_true", help="useful informations")

        args = parser.parse_args()

        if args.info == True:
            from rich import print

            print("archdots\n")
            print("{: <20}: {}".format("config folder", CONFIG_FOLDER))
            print("{: <20}: {}".format("cache folder", CACHE_FOLDER))
            print("{: <20}: {}".format("chezmoi folder", CHEZMOI_FOLDER))
            print("{: <20}: {}".format("recognized platform", PLATFORM))
            exit()

        run_command(args, metadata_dict, parser_dict)

        save_parser_cache(CACHE_FOLDER, command_tree_json, metadata_dict)

    except (
        PackageException,
        PackageManagerException,
        ParseException,
        GuiException,
        SettingsException,
        CommandException,
    ) as e:
        from rich.console import Console

        console = Console(stderr=True, style="bold red", markup=False, highlight=False)

        console.print(e)
        os._exit(1)
    except KeyboardInterrupt:
        pass
