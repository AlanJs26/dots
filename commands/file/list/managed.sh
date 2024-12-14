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

show_managed() {
  eval "data=(${args[folder]})"

  if [[ ${args[tree]} -eq 1 ]]; then
    if [ -z "$data" ] || [[ "$(readlink -f "$data")" = "$HOME" ]]; then
      tree -L $(get_level) --fromfile <(chezmoi managed | trailing_slash)
    else
      tree -L $(get_level) --fromfile <(chezmoi managed $data | trailing_slash)
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
