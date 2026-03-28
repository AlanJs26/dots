#/bin/env bash

: <<ARCHDOTS
help: shows unmanaged dotfiles
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

show_unmanaged() {
  eval "data=(${args[folder]})"
  # data=$(echo $data|sed "s:$HOME/::")

  if [[ ${args[tree]} -eq 1 ]]; then
    chezmoi unmanaged $data | tree -a -L $(get_level) --fromfile . --dirsfirst
  else
    chezmoi unmanaged $data
  fi
}

# echo ${args[level]}
show_unmanaged
