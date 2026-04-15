import re
from pathlib import Path

from dacite import from_dict
from dacite.exceptions import WrongTypeError
import yaml

from archdots.core.exceptions import ParseException
from archdots.schema import Metadata


def extract_metadata(filepath: str | Path):
    filepath = Path(filepath)
    if filepath.is_dir():
        return Metadata(help=f"{filepath.stem} help")

    with open(filepath, "r") as f:
        content = f.read()

    match = next(
        map(
            lambda x: x.strip(),
            re.findall(r"ARCHDOTS(.+?)ARCHDOTS", content, flags=re.DOTALL),
        ),
        None,
    )

    if not match:
        return Metadata(help=f"{filepath.stem} help")

    try:
        return from_dict(Metadata, yaml.safe_load(match))
    except WrongTypeError as e:
        raise ParseException(str(e), str(filepath))
