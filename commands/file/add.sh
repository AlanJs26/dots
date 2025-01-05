#/bin/env bash

: <<ARCHDOTS
help: adds files to chezmoi
arguments:
  - name: target_files
    required: true
    type: str
    nargs: +
    help: files to add
ARCHDOTS

gum spin --title="Adding ${args[target_files]}..." -- chezmoi add ${args[target_files]}
