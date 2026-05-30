"""Type aliases and common types used across archdots."""

from typing import TypeVar, ParamSpec, Any

# Generic type variables
T = TypeVar("T")  # function return value
P = ParamSpec("P")  # function parameters

# Common mappings
ConfigDict = dict[str, Any]
"""Type alias for configuration dictionaries."""
