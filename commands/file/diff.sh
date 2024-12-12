#/bin/env bash

: <<ARCHDOTS
help: isso é uma mensagem de ajuda
arguments:
  - name: group
    required: false
    type: str
    nargs: 2
    help: ajuda de group
flags:
  - long: --list
    short: -l
    type: bool
    help: isso é uma lista
ARCHDOTS

echo "${args[group]}"
