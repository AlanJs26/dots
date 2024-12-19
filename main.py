import os
from pydantic import ValidationError
from src.argparsing import ParseException, parse_folder, run_command
from src.package import PackageException
from src.constants import CONFIG_FOLDER, COMMANDS_FOLDER


def main():
    """
    archdots entrypoint
    """
    roots = [".", CONFIG_FOLDER]
    parser, depths = parse_folder(roots, os.path.basename(COMMANDS_FOLDER))
    args = parser.parse_args()

    run_command(args, os.path.basename(COMMANDS_FOLDER), roots, depths)


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
