# mud

![Version](https://img.shields.io/pypi/v/mud-git?logo=python)
![AUR Version](https://img.shields.io/aur/version/mud-git?logo=archlinux)
[![Test projects integrity](https://github.com/jasursadikov/mud/actions/workflows/test.yaml/badge.svg)](https://github.com/jasursadikov/mud/actions/workflows/test.yaml)
[![Publish Python Package](https://github.com/jasursadikov/mud/actions/workflows/publish-pypi.yaml/badge.svg)](https://github.com/jasursadikov/mud/actions/workflows/publish-pypi.yaml)
[![Publish to AUR](https://github.com/jasursadikov/mud/actions/workflows/publish-aur.yaml/badge.svg)](https://github.com/jasursadikov/mud/actions/workflows/publish-aur.yaml)

![Demo](./img.png)

mud is CLI utility that allows you to run git commands in multiple repositories. It has multiple powerful filtering tools, native commands with an informative terminal output and support of aliasing. This tool is not limited to git commands only; you can run any commands you wish. However, this tool was primarily designed to be used with git, so each referenced directory should have a `.git` directory.

## Installing
**PyPI**
```bash
pip install mud-git
```
**ArchLinux**
```bash
paru -S mud-git
```

For requirements check [requirements.txt](requirements.txt).

## Getting started

1. Run `mud config` to start an interactive wizard that helps you set the preferred settings. Check the [settings](#settings) section for more details. At the end, a `.mudsettings` file will appear in your home directory, which you can modify in the future.
2. Navigate to your preferred directory with repositories.
3. Run the `mud init` command to create a `.mudconfig` file. This file is important for keeping references to repositories. All repositories in the current directory will be included in `.mudconfig`.
4. Optional: Run [`mud set-global`](#commands) to make the current configuration default and accessible from any directory.

All entries are stored in `.mudconfig` in TSV format. After making your first entry, you can open `.mudconfig` in a text editor and modify it according to your needs.

Now you're able to run any command. Some examples:
```bash
# Fetch all repositories
mud git fetch
# Switching all repositories to a "master" branch
mud git checkout master
# Alternatively, you can filter only repos on non-master branch and switch them to master
mud --not-branch=master git checkout master
# Pull all diverged branches
mud --diverged git pull
```

## Using

### Commands
| Command                         | Description                                                                                                                       |
|---------------------------------|-----------------------------------------------------------------------------------------------------------------------------------|
| `mud set-global`                | sets the current `.mudconfig` as a global configuration so it will be used as a fallback configuration to run from any directory. |
| `mud get-config`                | prints the current `.mudconfig` location.                                                                                         |
| `mud prune`                     | removes all invalid repositories from the `.mudconfig`.                                                                           |
| `mud info`/`mud i`              | displays branch divergence and working directory changes.                                                                         |
| `mud status`/`mud st`           | displays working directory changes.                                                                                               |
| `mud log`/`mud l`               | displays the latest commit message, its time, and its author.                                                                     |
| `mud labels`/`mud lb`           | displays mud labels across repositories.                                                                                          |
| `mud branches`/`mud br`         | displays all branches in repositories.                                                                                            |
| `mud remote-branches`/`mud rbr` | displays all remote branches in repositories.                                                                                     |
| `mud tags`/`mud t`              | displays git tags in repositories.                                                                                                |

### Flags

`mud <FLAG> <COMMAND>` will execute a bash command across all repositories.

| Flag                                     | Description                                                                          |
|------------------------------------------|--------------------------------------------------------------------------------------|
| `-n=<str>` or `--name=<str>`             | includes repositories that contains provided string.                                 |
| `-l=<label>` or `--label=<label>`        | includes repositories with the provided label.                                       |
| `-L=<label>` or `--not-label=<label>`    | excludes repositories with the provided label.                                       |
| `-b=<branch>` or `--branch=<branch>`     | includes repositories with the provided branch.                                      |
| `-B=<branch>` or `--not-branch=<branch>` | excludes repositories with the provided branch.                                      |
| `-c` or `--command`                      | explicit command argument. Use this whenever you're trying to run a complex command. |
| `-m` or `--modified`                     | filters out modified repositories.                                                   |
| `-d` or `--diverged`                     | filters repositories with diverged branches.                                         |
| `-t` or `--table`                        | toggles the default table view setting for execution.                                |
| `-a` or `--async`                        | toggles the asynchronous execution feature.                                          |

Example:

```bash
# Filters out all repos with the master branch and diverged branches and then runs the pull command.
mud -b=master -d git pull

# Fetches all repositories that are not on the master branch and have the "personal" label, excluding those with the "work" label.
mud -B=master -l=personal -L=work git fetch
```

## Settings

Settings are stored at `~/.config/mud/settings.ini`.

| Key                      | Value                    | Description                                                                      |
|--------------------------|--------------------------|----------------------------------------------------------------------------------|
| `run_async`              | `True`/`False`           | enables asynchronous commands.                                                   |
| `run_table`              | `True`/`False`           | enables table view for asynchronous commands. Requires `run_async`.              |
| `nerd_fonts`             | `True`/`False`           | enables nerd fonts in the output.                                                |
| `display_borders`        | `True`/`False`           | enables borders in the table view.                                               |
| `display_headers`        | `True`/`False`           | enables headers in the table view.                                               |
| `display_absolute_paths` | `True`/`False`           | displays absolute paths for directories.                                         |
| `round_corners`          | `True`/`False`           | enables round corners for the table view. Requires `show_borders` to be enabled. |
| `collapse_paths`         | `True`/`False`           | simplifies branch names in the branch view.                                      |
| `config_path`            | `~/Documents/.mudconfig` | this is set by the `mud set-global` command.                                     |

### Aliases

You can create your own aliases. To do so, edit the `[alias]` section of the `.mudsettings` file. The `.mudsettings` file has the following aliases by default:
```ini
[alias]
to = git checkout
fetch = git fetch
pull = git pull
push = git push
```

## Labeling

You can modify your `.mudconfig` file using the following commands:

| Command                     | Description                                    |
|-----------------------------|------------------------------------------------|
| `mud add <path>`            | adds a path without a label.                   |
| `mud add <path> <label>`    | adds a path with an optional label.            |
| `mud remove <path>`         | removes the directory with the specified path. |
| `mud remove <path> <label>` | removes the label from a directory.            |
