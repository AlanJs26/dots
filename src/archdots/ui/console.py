"""Console I/O utilities."""

from typing import Any
from rich.console import Console
from rich.prompt import Confirm, Prompt
from contextlib import contextmanager
from rich.progress import Progress

# Standard console instances
warn_console = Console(style="yellow italic", stderr=True)
err_console = Console(style="red", stderr=True)


def title(*content: Any, color="cyan") -> str:
    """Format a title string with color and separators.

    Args:
        *content: Text sections to format
        color: Rich color name (default: cyan)

    Returns:
        Formatted title string
    """
    return " ".join([f"[{color}]::[/]", *content])


def print_title(*content: Any, color="cyan"):
    """Print a formatted title to console.

    Args:
        *content: Text sections to format
        color: Rich color name (default: cyan)
    """
    from rich import print

    print(title(*content, color=color))


def confirm(message: str, color="cyan", **kwargs) -> bool:
    """Prompt user for yes/no confirmation.

    Args:
        message: Prompt message
        color: Rich color name (default: cyan)
        **kwargs: Additional arguments to pass to Confirm.ask()

    Returns:
        True if user confirms, False otherwise
    """
    return Confirm.ask(f"[{color}]:: [/]" + message, **kwargs)


def prompt(message: str, color="cyan", **kwargs) -> str:
    """Prompt user for text input.

    Args:
        message: Prompt message
        color: Rich color name (default: cyan)
        **kwargs: Additional arguments to pass to Prompt.ask()

    Returns:
        User input string
    """
    return Prompt.ask(f"[{color}]:: [/]" + message, **kwargs)


@contextmanager
def transient_progress(description: str):
    """Context manager for transient progress bar.

    Args:
        description: Progress description text

    Yields:
        Rich Progress object
    """
    with Progress(transient=True) as progress:
        progress.add_task(str(description), total=None)
        yield
