from enum import Enum
from typing import Optional
from pydantic import BaseModel

class ArgumentTypeEnum(Enum):
    str = 'str'
    bool = 'bool'
    int = 'int'

class ParserArgument(BaseModel):
    name: str
    required: bool = False
    type: ArgumentTypeEnum = ArgumentTypeEnum.str
    help: str
    nargs: Optional[str|int] = None

class ParserFlag(BaseModel):
    long: str
    short: Optional[str] = None
    required: bool = False
    type: ArgumentTypeEnum = ArgumentTypeEnum.str
    nargs: Optional[str|int] = None
    help: str

class ParserConfig(BaseModel):
    help: str
    arguments: list[ParserArgument] = []
    flags: list[ParserFlag] = []

