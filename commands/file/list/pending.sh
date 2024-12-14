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

show_pending() {
  from_git="$(archdots git diff --cached --numstat | awk '{print $3}' | rg 'dot_' -r '.' --passthrough | sed 's/private_|executable_//g')"
  from_chezmoi="$(chezmoi diff | rg 'diff --git' | rg 'a/(.+) b/' -o -r '$1')"

  pending="$(echo -e "$from_git\n$from_chezmoi" | sort -u)"

  if [[ ${args[tree]} -eq 1 ]]; then
    tree -L $(get_level) --fromfile <(cat <<<"$pending" | trailing_slash)
  else
    cat <<<"$pending"
  fi
}

show_pending
