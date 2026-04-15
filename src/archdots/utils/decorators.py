"""Utilities for caching and metaclasses."""

import inspect
import functools
from abc import ABCMeta
from collections.abc import Callable
from typing import TypeVar, ParamSpec

T = TypeVar("T")  # function return value
P = ParamSpec("P")  # function parameters

_memo = {}


class SingletonMeta(ABCMeta):
    """Metaclass for singleton pattern implementation."""

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


def memoize(f: Callable[P, T]) -> Callable[P, T]:
    """Decorator to cache function results based on use_memo parameter.

    The decorated function MUST have a 'use_memo' boolean parameter (default or explicit).
    If use_memo=True, result is cached; if use_memo=False, function runs fresh each time.
    """

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
                "memoize expects the 'use_memo' argument to be a boolean"
            )

        if f not in _memo:
            _memo[f] = {}

        if use_memo and args in _memo[f]:
            return _memo[f][args]
        else:
            _memo[f][args] = f(*args, **kwargs)
            return _memo[f][args]

    return wrapper
