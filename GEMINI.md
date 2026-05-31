# archdots

`archdots` is a command-line application designed to manage dotfiles and system packages declaratively, primarily using Python and `chezmoi`.

## Project Overview

- **Purpose:** Synchronize system configuration (dotfiles) and installed packages across multiple machines.
- **Core Technologies:** 
    - **Python:** Primary language.
    - **uv:** Project and dependency management.
    - **chezmoi:** Backend for dotfile synchronization.
    - **rich:** Terminal UI and formatting.
    - **lark:** Parsing logic for custom package definitions (PKGBUILDs).
    - **hatchling:** Build backend.

## Architecture

- **Dynamic Command Loading:** Commands are discovered at runtime from `src/archdots/commands/` (shipped with the package) and `~/.config/archdots/commands` (user-defined). Subfolders create subcommands.
- **Platform Abstraction:** Located in `src/archdots/core/platforms/`, defining behaviors for Linux distributions (Arch, Debian, Fedora, Ubuntu) and Windows.
- **Package Management:** Supports multiple managers (`apt`, `pacman`, `winget`, `scoop`, `uv`, `npm`) via a unified interface in `src/archdots/packages/managers/`.
- **Custom Packages (PKGBUILD):** A custom syntax inspired by Arch Linux for defining packages and health scripts that aren't available in standard repositories.

## Building and Running

### Development
- **Setup:** Ensure `uv` is installed. Run `uv sync` to install dependencies.
- **Run:** Use `uv run runner.py [command]` to run the CLI in development mode.
- **GUI:** The project includes a work-in-progress GUI built with `PySide6`, accessible via `uv run runner.py gui`.

### Production
- **Installation:** `pip install .` installs the `dots` command globally.
- **Main Command:** `dots` is the entry point.

## Development Conventions

- **Command Metadata:** New commands (scripts in `commands/`) must include a metadata header between `ARCHDOTS` markers for help messages, arguments, and flags.
    ```python
    """
    ARCHDOTS
    help: describe your command here
    arguments:
      - name: my_arg
        required: true
    ARCHDOTS
    """
    ```
- **Platform Specificity:** When adding new functionality, check if it should be platform-agnostic or implemented within the `Platform` hierarchy.
- **UI:** Use the `rich` library for all console output to maintain a consistent aesthetic. `archdots.ui.console` provides pre-configured consoles and helpers.
- **Exceptions:** Use custom exceptions defined in `archdots.core.exceptions` for better error reporting.

## Key Files & Directories

- `src/archdots/`: Core application logic.
- `commands/`: Default CLI commands.
- `chezmoi_template/`: Templates used for initializing `chezmoi`.
- `default_packages/`: Pre-defined PKGBUILDs for essential tools.
- `pyproject.toml`: Dependency and build configuration.
- `runner.py`: Convenient entry point for development.
