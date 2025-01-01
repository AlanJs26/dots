#/bin/env bash

: <<ARCHDOTS
help: sync apps and dots
arguments:
  - name: type
    required: false
    type: str
    choices: ['pkgs', 'dots']
    help: specify type of synching. Leave empty for both
ARCHDOTS

# for x in "${!args[@]}"; do printf "[%s]=%s\n" "$x" "${args[$x]}"; done

if [ -z "${args[type]}" ] || [ "${args[type]}" = "pkgs" ]; then
  $ARCHDOTS pkgs sync
fi

if [ -z "${args[type]}" ] || [ "${args[type]}" = "dots" ]; then
  $ARCHDOTS file sync
fi
