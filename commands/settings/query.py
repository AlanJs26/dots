"""
ARCHDOTS
help: query settings using jq syntax
arguments:
  - name: input
    required: true
    type: str
    help: query
ARCHDOTS
"""

# this prevents the language server to throwing warnings
args = args  # type: ignore

from src.settings import read_config
import yaml
import os

yaml_config = yaml.dump(read_config())

os.system(
    f"""(
cat <<EOF
{yaml_config}
EOF
) |yq {args['input']}"""
)
