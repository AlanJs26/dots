"""
ARCHDOTS
help: uninstall packages, independently of managed state
arguments:
    - name: package
      required: True
      type: str
      nargs: +
      help: name
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

from archdots.package_manager import split_packages_by_pm

pkgs_by_pm = split_packages_by_pm(args["package"])
for pm, pkgs in pkgs_by_pm.items():
    pm.uninstall(pkgs)
