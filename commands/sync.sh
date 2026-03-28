#/bin/env bash

: <<ARCHDOTS
help: sync packages and/or files
arguments:
  - name: type
    required: false
    type: str
    choices: ['pkgs', 'files']
    help: specify type of synching. Leave empty for both
flags:
  - long: --commit
    type: bool
    help: do not re-add files, only do a commit/push
ARCHDOTS

# for x in "${!args[@]}"; do printf "[%s]=%s\n" "$x" "${args[$x]}"; done
if [ -z "${args[type]}" ] || [ "${args[type]}" = "pkgs" ]; then
  $ARCHDOTS pkg _sync
fi

if [ -z "${args[type]}" ] || [ "${args[type]}" = "files" ]; then
  if [ "${args[commit]}" = "0" ]; then
    $ARCHDOTS file _sync
  else
    $ARCHDOTS file _sync --commit
  fi
fi
