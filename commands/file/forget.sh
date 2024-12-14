#/bin/env bash

: <<ARCHDOTS
help: Remove a target from the source state
arguments:
  - name: file
    required: true
    type: str
    nargs: +
    help: files/folders to forget
ARCHDOTS

bash -c "chezmoi forget ${args[file]}"
