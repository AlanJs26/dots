"""
ARCHDOTS
help: configure health scripts
arguments:
  - name: name
    required: false
    type: str
    nargs: "*"
    help: script to configure
flags:
    - long: --force
      type: bool
      help: force configuration
    - long: --unconfigure
      type: str
      nargs: +
      help: unconfigure one or more scripts
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

from rich import print

from archdots.ui.console import print_title
from archdots.packages.package import get_packages
from archdots.core.constants import HEALTH_FOLDER
from archdots.packages.dependencies import split_packages_by_pm


health_scripts = get_packages(HEALTH_FOLDER)
all_packages = [
    pkg for pkg in health_scripts if not pkg.check(supress_output=True) or args["force"]
]

packages_by_name = {pkg.name: pkg for pkg in all_packages}

if args["unconfigure"]:
    for name in args["unconfigure"]:
        if name not in packages_by_name:
            print(f'unknown health script "{name}"')
            exit()
    selected_packages = [packages_by_name[pkg_name] for pkg_name in args["name"]]
elif args["name"]:
    for name in args["name"]:
        if name not in packages_by_name:
            print(f'unknown health script "{name}"')
            exit()
    selected_packages = [packages_by_name[pkg_name] for pkg_name in args["name"]]
else:
    selected_packages = all_packages


if not all_packages:
    if not health_scripts:
        print("[yellow]there are any health scripts to configure")
    else:
        print("[green]all health scripts are configured!")
    exit()


for pkg in selected_packages:
    if args["unconfigure"]:
        print_title(f'Unconfiguring "{pkg.name}"')
        if not pkg.uninstall():
            print_title(f'Failed to unconfigure "{pkg.name}', color="red")
    else:
        print_title(f'Configuring "{pkg.name}"')

        print_title(f"Installing dependencies", color="yellow")
        for pm, deps in split_packages_by_pm(pkg.depends).items():
            if deps := list(set(deps).difference(pm.get_installed(use_memo=True))):
                pm.install(deps, force=args["force"])

        if not pkg.install(force=True):
            print_title(f'Failed to configure "{pkg.name}', color="red")


