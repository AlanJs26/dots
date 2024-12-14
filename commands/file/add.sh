#/bin/env bash

: <<ARCHDOTS
help: adds files to chezmoi
arguments:
  - name: file
    required: true
    type: str
    nargs: +
    help: files to add
ARCHDOTS

bash -c "gum spin --title='Adding ${args[file]}...' -- chezmoi add ${args[file]}"
