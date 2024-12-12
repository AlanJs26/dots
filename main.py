import os
from pydantic import ValidationError
from src.argparsing import ParseException, parse_folder, run_command
from src.package import (
    get_packages,
    package_from_path,
    PackageException,
)


def main():
    """
    archdots entrypoint
    """
    root = "commands"
    parser, depths = parse_folder([root])
    args = parser.parse_args()

    # print(args)
    run_command(args, root, depths)
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
        print(e)
        os._exit(1)
