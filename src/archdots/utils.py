from typing import Callable
from urllib.parse import urlparse
from decorator import decorator


class ParseException(Exception):
    pass


class GuiException(Exception):
    pass


class PackageException(Exception):
    def __init__(self, message, pkg_name="") -> None:
        import re

        if pkg_name:
            message = f"Exception for '{pkg_name}' package\n{message}"
        super().__init__(re.sub(r"^\s+", "", message, flags=re.MULTILINE))


class PackageManagerException(Exception):
    pass


class SettingsException(Exception):
    pass


class SingletonMeta(type):
    """
    Metaclasse para implementar o padrão Singleton.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            # Cria a instância e armazena no dicionário
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


_memo = {}


@decorator
def memoize(f: Callable, *args, **kwargs):
    global _memo
    if not len(args) or not isinstance(args[-1], bool):
        raise ValueError(
            "memoize expect the last argument to be a boolean, i.e. use_memo"
        )
    use_memo = args[-1]
    if f not in _memo:
        _memo[f] = {}

    if use_memo and args in _memo[f]:
        return _memo[f][args]
    else:
        _memo[f][args] = f(*args, **kwargs)
        return _memo[f][args]


def is_url_valid(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except AttributeError:
        return False


class CommandException(Exception):
    pass
