"""Shared ruamel.yaml instance for round-trip YAML processing."""

from ruamel.yaml import YAML

# Configure YAML for round-trip with preservation of quotes and specific indentation
yaml_rt = YAML()
yaml_rt.preserve_quotes = True
yaml_rt.indent(mapping=2, sequence=4, offset=2)
# Ensure we use the round-trip loader/dumper by default
yaml_rt.typ = "rt"
