import os
import inspect
import functools
from pathlib import Path
from urllib.parse import urlparse
from collections.abc import Callable
from typing import TypeVar, ParamSpec

from archdots.constants import PLATFORM


def default_editor(file: Path | str):
    if PLATFORM == "windows":
        import webbrowser

        webbrowser.open(str(file))
        # os.system(f'"{file}"')
    else:
        os.system(f'$EDITOR "{file}"')


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


_memo = {}

T = TypeVar("T")  # function return value
P = ParamSpec("P")  # function parameters


def memoize(f: Callable[P, T]) -> Callable[P, T]:

    @functools.wraps(f)
    def wrapper(*args: P.args, **kwargs: P.kwargs):
        global _memo

        # Retrieve default arguments from original function
        signature = inspect.signature(f)
        bound_args = signature.bind(*args, **kwargs)
        bound_args.apply_defaults()  # apply default values

        use_memo = bound_args.arguments.get("use_memo")

        if use_memo is None or not isinstance(use_memo, bool):
            raise ValueError(
                "memoize expect the last argument to be a boolean, i.e. use_memo"
            )

        if f not in _memo:
            _memo[f] = {}

        if use_memo and args in _memo[f]:
            return _memo[f][args]
        else:
            _memo[f][args] = f(*args, **kwargs)
            return _memo[f][args]

    return wrapper


def is_url_valid(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except AttributeError:
        return False
