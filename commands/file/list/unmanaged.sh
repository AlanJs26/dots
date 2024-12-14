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
  - long: --fast
    type: bool
    help: do not distinguish folders from files in tree view
  - long: --tree
    type: bool
    help: display folders as a tree
ARCHDOTS

function trailing_slash() {
  if [[ -z "${args[fast]}" ]]; then
    cat </dev/stdin | xargs -i sh -c '[ "$(file --brief "$HOME/{}")" = "directory" ]&&echo "{}/"||echo {}'
  else
    cat </dev/stdin
  fi
}

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
    tree -L $(get_level) --fromfile <(chezmoi unmanaged $data | trailing_slash)
  else
    chezmoi unmanaged $data
  fi
}

# echo ${args[level]}
show_unmanaged
