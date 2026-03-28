#/bin/env bash

: <<ARCHDOTS
help: shows pending dotfiles
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

show_pending() {
  from_git="$(chezmoi git -- diff --cached --numstat | awk '{print $3}' | rg 'dot_' -r '.' --passthrough | sed 's/private_|executable_//g')"
  from_chezmoi="$(chezmoi diff | rg 'diff --git' | rg 'a/(.+) b/' -o -r '$1')"

  pending="$(echo -e "$from_git\n$from_chezmoi" | awk '{print "~/"$0}' | sort -u)"

  if [[ ${args[tree]} -eq 1 ]]; then
    cat <<<"$pending" | tree -a -L $(get_level) --fromfile . --dirsfirst
  else
    cat <<<"$pending"
  fi
}

show_pending
