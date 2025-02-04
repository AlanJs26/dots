"""
ARCHDOTS
help: query settings using jq syntax
arguments:
  - name: input
    required: true
    type: str
    help: query
flags:
  - long: --raw
    type: bool
    help: do not pretty print in json
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

from archdots.settings import read_config
import yaml
import os

yaml_config = yaml.dump(read_config())

extra_args = ""
if args["raw"]:
    extra_args = "--raw-output"
    pass

os.system(
    f"""(
cat <<EOF
{yaml_config}
EOF
) |yq '{args['input']}' {extra_args}"""
)
