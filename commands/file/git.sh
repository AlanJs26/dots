#/bin/env bash

: <<ARCHDOTS
help: run git commands from chezmoi repo
arguments:
  - name: args
    required: true
    type: str
    nargs: "*"
    help: 'custom arguments. To input long flags (i.e. --flag) you must insert "--" at the begining of the arguments. Ex: git -- status --staged'
ARCHDOTS

cd ~/.local/share/chezmoi
git ${args[@]}
