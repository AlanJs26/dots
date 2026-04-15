"""Progress indicators and decorators."""

import functools
from collections.abc import Callable
from typing import TypeVar, ParamSpec
from rich.progress import Progress

T = TypeVar("T")  # function return value
P = ParamSpec("P")  # function parameters


def progress_decorator(description: str):
    """Decorator to show transient progress while function runs.

    Args:
        description: Description text for progress bar

    Returns:
        Decorated function
    """

    def decorator(f: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs):
            with Progress(transient=True) as progress:
                progress.add_task(str(description), total=None)
                return f(*args, **kwargs)

        return wrapper

    return decorator
