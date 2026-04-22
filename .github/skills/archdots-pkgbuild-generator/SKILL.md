---
name: archdots-pkgbuild-generator
description: 'Generate functional archdots PKGBUILD files from natural-language descriptions. Use for creating package installers or health scripts with install/uninstall/check functions, required metadata fields (description/url/depends/source/platform), platform-aware shell code (bash or powershell), and validation checklist.'
argument-hint: 'Describe what the PKGBUILD should install or configure, target platform, dependencies, and optional sources.'
user-invocable: true
disable-model-invocation: false
---

# Archdots PKGBUILD Generator

Create a functional `PKGBUILD` for archdots from a user description.

## When to Use
- The user asks to create a new package `PKGBUILD`.
- The user asks to create a health script `PKGBUILD`.
- The user describes desired install behavior and wants install/uninstall/check functions.
- The user needs platform-specific package configuration (`linux` or `windows`).

## Core Rules
- This PKGBUILD format is archdots-specific, not Arch Linux PKGBUILD.
- The file has global metadata variables and root-level functions.
- Only these root functions are supported:
1. `install`
2. `uninstall`
3. `check`
- Global metadata variables are not directly accessible as runtime variables in functions.
- Function bodies must be self-sufficient and deterministic.
- Always prefer installing dependencies through `depends` metadata.
- Never emit explicit dependency install commands inside functions (for example `winget install ...`, `apt install ...`, `pacman -S ...`).

## Required Global Fields
Always include these fields in the generated PKGBUILD:
1. `description`
2. `url`
3. `depends`
4. `source`
5. `platform`

### User Decisions (Locked)
1. `platform` must be a single value (`linux` or `windows`).
2. `url` may be empty.
3. When no sources are required, use an empty variable tuple format: `source=()`.
4. Dependency installation must be modeled in `depends`, not hardcoded in script functions.
5. Generated PKGBUILD must be written directly to the package file path (not only returned as text).

### Field Semantics
- `description`: human-readable summary of what the PKGBUILD does.
- `url`: optional metadata for documentation/repository page. Empty is allowed.
- `depends`: space-separated dependencies, each in format `package_manager:package_name`.
- `source`: space-separated external resources to download. If none, use `source=()`.
- `platform`: must be a single value, `linux` or `windows`.

## Procedure
1. Classify intent.
- If user asks to install an application/package: produce package installer behavior.
- If user asks to configure system behavior (for example prompt/theme/tool config): produce health script behavior.

2. Determine platform and shell style.
- `platform=linux` -> functions should use bash-compatible commands.
- `platform=windows` -> functions should use PowerShell-compatible commands.

3. Resolve destination path and write mode.
- Always create or update the target `PKGBUILD` file directly.
- Config folder `~/.config/archdots`
- If context clearly identifies package folder/name, write there.
- If context is unclear:
1. Package PKGBUILD default folder: `<root>/packages/<package-name>/PKGBUILD`
2. Health PKGBUILD default folder: `<root>/health/<script-name>/PKGBUILD`

4. Resolve dependencies and sources.
- Populate `depends` using `pm:name` format.
- Put external package requirements in `depends` instead of manual install commands in `install`.
- Populate `source` with external URLs only when needed.
- If there are no external resources, use `source=()`.
- Assume downloaded sources are exposed to scripts via `sourced` absolute paths.

5. Generate function contract.
- `check`: returns success when desired final state is already configured/installed.
- `install`: applies idempotent setup and reaches state validated by `check` without directly installing dependency packages.
- `uninstall`: reverses installation/configuration safely.

6. Apply type-specific behavior.
- Package PKGBUILD:
1. `install` performs setup steps that are not dependency package installation.
2. `uninstall` removes software.
3. `check` verifies software presence/version/state.
- Health PKGBUILD:
1. `install` applies configuration.
2. `uninstall` reverts configuration.
3. `check` verifies config state.

7. Validate before returning.
- Confirm all required global fields exist.
- Confirm only supported functions exist.
- Confirm dependency format is valid.
- Confirm platform matches command syntax.
- Confirm `check` reflects the target state that `install` establishes.
- Confirm dependency package installation is represented in `depends` and not hardcoded in script body.
- Confirm PKGBUILD has been written/updated in the target file path.

## Decision Matrix
1. Package install request:
- Prefer dependency declaration through `depends` for package installation requirements.
- Do not place package-manager dependency installation commands in function bodies.
- Keep `install/uninstall/check` scoped to package lifecycle.

2. Health script request:
- Focus on stateful config changes and reversibility.
- `check` must verify the exact configuration state.

3. Sources needed:
- Use `source` and consume from `sourced` paths.
- Avoid hardcoding temp directories.

## Output Format
Default behavior:
1. Write/update the PKGBUILD directly in the correct path.
2. Return a concise summary including the file path written.

If the user explicitly asks for inline content only, provide the PKGBUILD body as text.

## Quality Checklist
- Contains `description`, `url`, `depends`, `source`, `platform`.
- Contains exactly `install`, `uninstall`, `check` functions.
- `depends` entries use `pm:pkg` format.
- `platform` is exactly one of `linux` or `windows`.
- Empty `url` is accepted when no reference link is available.
- Empty source is represented as `source=()`.
- `check` is deterministic and aligned with install target state.
- `install` and `uninstall` are idempotent-safe where possible.
- Dependency package installs are not hardcoded in function bodies.
- PKGBUILD is written/updated directly in root path (`~/.config/archdots`).

## Example Prompts
- "Crie um PKGBUILD para instalar Starship no Windows via winget."
- "Crie um health script para configurar Starship Prompt no PowerShell."
- "Gere um PKGBUILD Linux para configurar zsh com plugin X e check de integridade."
