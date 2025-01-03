# 🚀 Archdots

> Manage your dotfiles and packages in one place

---

Archdots is a command-line application designed to help you back up and maintain your system configuration inside a GitHub repository.

Once everything is set up, simply run `dots sync`, and all files and packages will be synchronized.

In addition, all CLI commands are crafted to be easily extensible, allowing you to tweak the tool for your specific needs.

---

## ✨ Features

### 📜 Declarative Configuration

Files are managed by **chezmoi**, and packages are stored in a configuration file. This makes it simple to replicate your setup on another machine or restore it from a backup.

### 🛠️ Custom Packages and Scripts

With a syntax inspired by Arch Linux's package declaration, you can create scripts for packages that aren't available through your package manager.

### ⚡ Extendability

Any script placed in the `commands` folder will automatically become available in the CLI, consolidating all your bash/python scripts in one place.

---

## 🛠️ Installation

Clone the repository and install it using pip:

```bash
$ pip install .  
```

> ⚠️ In the future, this project will be available on PyPI.

### 📦 Dependencies

Archdots uses **chezmoi** to manage dotfiles.  
To install chezmoi, follow the instructions on their [installation page](https://www.chezmoi.io/install/#one-line-package-install).

---

## 📚 How to Use

> For a detailed guide on all commands, check out our [GitHub Wiki](https://github.com/AlanJs26/dots).

---

### 🗂️ Files

#### Initialize chezmoi

Before using `archdots`, initialize chezmoi as described in their [Quick Start guide](https://www.chezmoi.io/quick-start/):

```bash
$ chezmoi init  
```

This creates a local git repository at `~/.local/share/chezmoi` where chezmoi stores its source state.

#### Add Files

When you add files, a copy is stored in your dotfiles repository. Re-running the add command updates the repository's state:

```bash
$ dots file add ~/.bashrc  
```

#### Sync Files

The `sync` command performs three actions:

1. Re-adds all files.
2. Creates a git commit.
3. Pushes changes to the repository.

```bash
$ dots file sync  
```

#### Set Up a New Machine

To set up a new machine, follow the instructions in the [chezmoi guide](https://www.chezmoi.io/quick-start/#set-up-a-new-machine-with-a-single-command), or run:

```bash
$ chezmoi init --apply https://github.com/$GITHUB_USERNAME/dotfiles.git  
```

---

### 📦 Packages

Packages can be in one of four states:

|**State**|**Installed**|**Present in `config.yaml`**|
|---|---|---|
|Managed|✅|✅|
|Unmanaged|✅|❌|
|Pending|❌|✅|
|Lost|❌|❌|

> ⚠️ The **Lost** state only applies to custom packages.

For an ideal setup, all packages should be in the **Managed** state.

#### Unmanaged Packages

Handle unmanaged packages by either deleting them or adding them to `config.yaml`. This is done interactively via the `review` command:

```bash
$ dots pkg review  
```

#### Pending Packages

The `sync` command installs pending packages and prompts you to review unmanaged ones when necessary:

```bash
$ dots pkg sync  
```

#### Custom Packages

Create custom packages using the `new` command, which prompts for necessary details and opens an editor:

```bash
$ dots pkg new  
```

> For more information on the syntax of custom packages, see the [wiki](https://github.com/AlanJs26/dots).

---

## 🔧 Extending

Add new commands by placing scripts in `~/.config/archdots/commands`.

- Nested folder structures can create subcommands.
- Default commands are in the `commands/` folder in the project root and can serve as examples.

#### Command Metadata

CLI command details (e.g., help messages) are defined in a script header marked with `ARCHDOTS`.  
Example from `dots settings query`:

```yaml
ARCHDOTS  
help: query settings using jq syntax  
arguments:  
  - name: input  
    required: true  
    type: str  
    help: query  
flags:  
  - long: --raw  
    type: bool  
    help: do not pretty print in json  
ARCHDOTS  
```

---

## 🙌 Contributing

1. **Fork the repository** – Start by forking this repository to your GitHub account.
2. **Create a branch** – Use a new branch for your changes.
3. **Make changes** – Implement your desired changes or fixes.
4. **Submit a PR** – Submit a pull request with a detailed description of your changes.

Contributions are always welcome—whether it's reporting issues, suggesting features, or submitting fixes!

---

## 🏆 Credits

Archdots is inspired by:

- [chezmoi](https://www.chezmoi.io/) – A powerful dotfile manager.
- [pacdef](https://github.com/steven-omaha/pacdef) – Managing packages declaratively on Linux.
- [bashly](https://bashly.dannyb.co/) – Building custom CLIs can be simple and enjoyable.

---

## 🛣️ Roadmap

- [ ]  Find a better name.
- [ ]  Improve documentation.
- [ ]  Add a GUI for managing files and packages.
- [ ]  Publish the project on PyPI.

