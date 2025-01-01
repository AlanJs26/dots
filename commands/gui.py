"""
ARCHDOTS
help: GUI for managing packages
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

from archdots.gui import main_gui

main_gui()
