#/bin/env bash

: <<ARCHDOTS
help: sync apps and dots
arguments:
  - name: type
    required: false
    type: str
    choices: ['apps', 'dots']
    nargs: 1
    help: specify type of synching. Leave empty for both
ARCHDOTS

for x in "${!args[@]}"; do printf "[%s]=%s\n" "$x" "${args[$x]}"; done
