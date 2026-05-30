#!/usr/bin/env sh

set -eu

REPO_TARBALL_URL="https://github.com/AlanJs26/dots/archive/refs/heads/main.tar.gz"
RUN_INIT=0

while [ "$#" -gt 0 ]; do
    case "$1" in
        --run-init)
            RUN_INIT=1
            ;;
        --repo-zip-url)
            shift
            REPO_TARBALL_URL="$1"
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
    shift
done

log_step() {
    printf '[dots-bootstrap] %s\n' "$1"
}

has_cmd() {
    command -v "$1" >/dev/null 2>&1
}

ensure_sudo() {
    if [ "$(id -u)" -eq 0 ]; then
        SUDO=""
    elif has_cmd sudo; then
        SUDO="sudo"
    else
        echo "This script needs root privileges to install Python. Run as root or install sudo." >&2
        exit 1
    fi
}

install_base_tools() {
    ensure_sudo
    log_step "Installing required base tools..."

    if has_cmd apt-get; then
        $SUDO apt-get update
        $SUDO apt-get install -y curl ca-certificates tar
    elif has_cmd dnf; then
        $SUDO dnf install -y curl ca-certificates tar
    elif has_cmd pacman; then
        $SUDO pacman -Sy --noconfirm curl ca-certificates tar
    elif has_cmd zypper; then
        $SUDO zypper --non-interactive install curl ca-certificates tar
    elif has_cmd apk; then
        $SUDO apk add --no-cache curl ca-certificates tar
    else
        echo "Could not detect a supported package manager for automatic base tool install." >&2
        exit 1
    fi
}

install_uv() {
    if has_cmd uv; then
        log_step "uv already available."
        return
    fi

    log_step "Installing uv..."
    if ! has_cmd curl && ! has_cmd wget; then
        install_base_tools
    fi

    if has_cmd curl; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
    elif has_cmd wget; then
        wget -qO- https://astral.sh/uv/install.sh | sh
    else
        echo "Neither curl nor wget was found. Cannot install uv automatically." >&2
        exit 1
    fi

    UV_LOCAL_BIN="$HOME/.local/bin"
    if [ -d "$UV_LOCAL_BIN" ]; then
        PATH="$UV_LOCAL_BIN:$PATH"
        export PATH
    fi

    if ! has_cmd uv; then
        echo "uv could not be installed automatically." >&2
        exit 1
    fi
}

install_dots() {
    log_step "Downloading project source archive..."

    TMP_ROOT="$(mktemp -d)"
    TAR_PATH="$TMP_ROOT/dots.tar.gz"
    SRC_ROOT="$TMP_ROOT/src"
    mkdir -p "$SRC_ROOT"

    if has_cmd curl; then
        curl -fsSL "$REPO_TARBALL_URL" -o "$TAR_PATH"
    elif has_cmd wget; then
        wget -qO "$TAR_PATH" "$REPO_TARBALL_URL"
    else
        echo "Neither curl nor wget was found. Cannot download project archive." >&2
        exit 1
    fi

    tar -xzf "$TAR_PATH" -C "$SRC_ROOT"

    PROJECT_DIR="$(find "$SRC_ROOT" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
    if [ -z "$PROJECT_DIR" ]; then
        echo "Could not find extracted project directory." >&2
        exit 1
    fi

    log_step "Installing dots via uv tool..."
    uv tool install --force "$PROJECT_DIR"

    log_step "Validating dots command..."
    uv tool run --from archdots dots --help >/dev/null
}

maybe_run_init() {
    if [ "$RUN_INIT" -ne 1 ]; then
        log_step "Skipping dots init. Use 'dots init' when you are ready."
        return
    fi

    log_step "Running dots init..."
    if has_cmd dots; then
        dots init
    else
        uv tool run dots init
    fi
}

log_step "Starting zero-dependency bootstrap for dots..."
install_uv
install_dots
maybe_run_init

printf '\n'
printf 'dots is installed.\n'
if has_cmd dots; then
    printf 'Try: dots --help\n'
else
    printf 'If dots is not found in this shell, open a new terminal and run: dots --help\n'
    printf 'Fallback in current shell: uv tool run dots --help\n'
fi
