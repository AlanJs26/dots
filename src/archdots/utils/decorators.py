"""Utilities for caching and metaclasses."""

import inspect
import functools
import threading
from abc import ABCMeta
from collections.abc import Callable
from typing import TypeVar, ParamSpec

T = TypeVar("T")  # function return value
P = ParamSpec("P")  # function parameters

_memo = {}
_memo_lock = threading.Lock()


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
    Thread-safe implementation.
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

        # Create a cache key from all bound arguments (tuple of items)
        # to ensure args and kwargs are both considered.
        cache_key = tuple(bound_args.arguments.items())

        with _memo_lock:
            if f not in _memo:
                _memo[f] = {}

            if use_memo and cache_key in _memo[f]:
                return _memo[f][cache_key]

        # Call the function outside the lock to allow other functions to be memoized
        # and to prevent deadlocks if the function itself calls something memoized.
        result = f(*args, **kwargs)

        with _memo_lock:
            _memo[f][cache_key] = result

        return result

    return wrapper
