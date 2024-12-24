import os
from pydantic import ValidationError
from src.argparsing import ParseException, parse_folder, run_command
from src.package import PackageException, get_packages
from src.constants import CONFIG_FOLDER, COMMANDS_FOLDER, PACKAGES_FOLDER
from src.gui import GuiException


def main():
    """
    archdots entrypoint
    """
    # roots = [".", CONFIG_FOLDER]
    # parser, depths = parse_folder(roots, os.path.basename(COMMANDS_FOLDER))
    # args = parser.parse_args()
    #
    # run_command(args, os.path.basename(COMMANDS_FOLDER), roots, depths)

    # packages = get_packages(PACKAGES_FOLDER)
    # from rich import print

    # print(packages)

    from src.gui import main_gui

    main_gui()


if __name__ == "__main__":
    try:
        main()
    except (PackageException, ParseException, ValidationError, GuiException) as e:
        from rich.console import Console

        console = Console()

        console.print(e, style="red")
        os._exit(1)
    except KeyboardInterrupt:
        pass
