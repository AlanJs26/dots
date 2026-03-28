#/bin/env bash

: <<ARCHDOTS
help: shows managed dotfiles
arguments:
  - name: folder
    required: false
    type: str
    nargs: "*"
    help: folders
flags:
  - long: --level
    type: int
    help: sets tree view max depth level
  - long: --tree
    type: bool
    help: display folders as a tree
ARCHDOTS

get_level() {
  if [[ -n "${args[level]}" ]]; then
    echo "${args[level]}"
    exit
  fi
  echo -e "99"
}

show_managed() {
  eval "data=(${args[folder]})"

  if [[ ${args[tree]} -eq 1 ]]; then
    if [ -z "$data" ] || [[ "$(readlink -f "$data")" = "$HOME" ]]; then
      chezmoi managed | tree -a -L $(get_level) --fromfile . --dirsfirst
    else
      chezmoi managed $data | tree -a -L $(get_level) --fromfile . --dirsfirst
    fi
  else
    if [ -z "$data" ] || [[ "$(readlink -f "$data")" = "$HOME" ]]; then
      chezmoi managed
    else
      chezmoi managed $data
    fi
  fi
}

show_managed
