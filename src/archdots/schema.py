from typing import Literal

from typing import Optional, Self
from pathlib import Path
import json
import dataclasses
from pydantic import BaseModel
from dataclasses import dataclass, field


@dataclass
class ParserArgument:
    name: str
    help: str
    required: bool = False
    type: Literal["str", "bool", "int"] = "str"
    # choices: list[str] = []
    choices: list[str] = field(default_factory=lambda: [])
    nargs: Optional[str | int] = None


@dataclass
class ParserFlag:
    long: str
    help: str
    short: Optional[str] = None
    required: bool = False
    type: Literal["str", "bool", "int"] = "str"
    nargs: Optional[str | int] = None
    # choices: list[str] = []
    choices: list[str] = field(default_factory=lambda: [])


class ParserCommandTreeNode(BaseModel):
    name: str
    subcommands: list[Self]
    path: Path
    mtime: float


class ParserConfig(BaseModel):
    help: str
    arguments: list[ParserArgument] = []
    flags: list[ParserFlag] = []


class ExtendedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, BaseModel):
            return o.model_dump_json()
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        if isinstance(o, Path):
            return str(o)
        return super().default(o)
