#/bin/env bash

: <<ARCHDOTS
help: Remove a target from the source state
arguments:
  - name: files
    required: true
    type: str
    nargs: +
    help: files/folders to forget
ARCHDOTS

chezmoi forget ${args[files]}
