import os
from pydantic import ValidationError
from src.argparsing import ParseException, parse_folder, run_command
from src.package import (
    get_packages,
    package_from_path,
    PackageException,
)
from src.settings import read_config
from pathlib import Path
from src.constants import CONFIG_FOLDER, COMMANDS_FOLDER


def main():
    """
    archdots entrypoint
    """
    roots = [".", CONFIG_FOLDER]
    parser, depths = parse_folder(roots, COMMANDS_FOLDER)
    args = parser.parse_args()

    # print(read_config())

    # print(args)
    run_command(args, COMMANDS_FOLDER, roots, depths)
    # print(get_packages("packages"))

    # packages_folder = "packages"
    # all_packages = [
    #     package_from_path(os.path.join(packages_folder, package_name))
    #     for package_name in get_packages(packages_folder)
    # ]

    # print(package_managers[0].get_installed())


if __name__ == "__main__":
    try:
        main()
    except (PackageException, ParseException, ValidationError) as e:
        from rich.console import Console

        console = Console()

        console.print(e, style="red")
        os._exit(1)
    except KeyboardInterrupt:
        pass
