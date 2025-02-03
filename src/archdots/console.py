from typing import Any
from rich.console import Console
from typing import TypeVar, ParamSpec
from collections.abc import Callable
import functools
from rich.progress import Progress

warn_console = Console(style="yellow italic", stderr=True)
err_console = Console(style="red", stderr=True)


def title(*content: Any, color="cyan"):
    return " ".join([f"[{color}]::[/]", *content])


def print_title(*content: Any, color="cyan"):
    from rich import print

    print(title(*content, color=color))


T = TypeVar("T")  # function return value
P = ParamSpec("P")  # function parameters


def transient_progress(description: str):

    def decorator(f: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs):

            with Progress(transient=True) as progress:
                progress.add_task(str(description), total=None)
                return f(*args, **kwargs)

        return wrapper

    return decorator
