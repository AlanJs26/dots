"""Integration with external editors and tools."""

import os
import webbrowser
from pathlib import Path

from archdots.core.platform import is_windows


def default_editor(file: Path | str):
    """Open a file in the default editor (platform-specific).

    On Windows: opens in the default web browser
    On Linux: uses $EDITOR environment variable
    """
    if is_windows():
        webbrowser.open(str(file))
    else:
        os.system(f'$EDITOR "{file}"')
