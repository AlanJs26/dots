from typing import Literal

from typing import Optional, Self
from pathlib import Path
import json
import dataclasses

from dataclasses import dataclass, field


@dataclass
class Argument:
    name: str
    help: str
    required: bool = False
    type: Literal["str", "bool", "int"] = "str"
    choices: list[str] = field(default_factory=lambda: [])
    nargs: Optional[str | int] = None


@dataclass
class Flag:
    long: str
    help: str
    short: Optional[str] = None
    required: bool = False
    type: Literal["str", "bool", "int"] = "str"
    nargs: Optional[str | int] = None
    choices: list[str] = field(default_factory=lambda: [])


@dataclass
class CommandTreeNode:
    name: str
    subcommands: list[Self]
    path: Path
    mtime: float


@dataclass
class Metadata:
    help: str
    arguments: list[Argument] = field(default_factory=lambda: [])
    flags: list[Flag] = field(default_factory=lambda: [])


class ExtendedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        if isinstance(o, Path):
            return str(o)
        return super().default(o)
