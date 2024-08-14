# mud

![Demo](img.png)

mud is a multi-directory git runner. Using this tool you can run git commands in a groups of repositories. This tool is not limited to git commands only, you can run any commands as you wish, but this tool was primarily designed to be used with git, so each referenced directory should have `.git`.

## Installing

1. Download (install.sh)[install.sh] script.
2. Run `install.sh` to install.

## Getting started

1. Run `mud configure`/`mud config` to run interactive wizard which will ask you to set the preferable settings. Check section [Settings](#settings) for more. This will create `.mudsettings` file in your home directory that you can alter in the future.
2. Locate to your preferable directory with multiple repositories.
3. Run `mud init` command to create `.mudconfig` file. This file is important to keep references to repositories. All repositories in current dictionary would be included to `.mudconfig`.
4. Run [`mud --set-global`](#global-mudconfig) to make current configuration default and reachable from any directory.

All entries are stored in `.mudconfig` in XML format. After making your first entry, you can open `.mudconfig` in a text editor and modify it according to your needs.

### Global .mudconfig
- `mud --set-global` - sets current `.mudconfig` as a global configuration, so it would be used as a fallback configuration to run from any directory.

## Using

### Commands
`mud <COMMAND>` will run command on all repositories. To filter repositories check [filtering](#filters) section.

- `mud info` - displays information in a compact table for all repositories.
- `mud status` - displays edit information for all repositories.
- `mud log` - displays log with information about repo's last commit, it's time and it's author.
- `mud labels` - displays labels for all repositories.
- `mud branch` - displays all branches in repositories.
- `mud tags` - displays git tags for all repositories.

### Arguments
- `-l=<label>` or `--label=<label>` - filters out repositories by mud labels.
- `-b=<branch>` or `--branch=<branch>` - filters out repositories by current branch name.
- `-m` or `--modified` - filters out modified repositories.
- `-d` or `--diverged` - filters repositories with diverged branches.
- `-t` or `--table` - toggles default table view setting for run.
```
Example:
mud -b=master -d git pull
# Filters out all repos with master branch and diverged branches and then runs pull command.
```

## Settings

Settings are stored in your home directory in `.mudsettings` file.

- `config_path = /home/user/path/.mudconfig` - this is set up by `mud --set-global` [command](#global-mudconfig).
- `nerd_fonts = 0/1` - toggles whenever nerd font icons should be used in output.
- `auto_fetch = 0/1` - when enabled, `mud status` and `mud log` do fetch for all repos when invoked.
- `run_async = 0/1` - enabled to run commands asynchronously.
- `run_table = 0/1` - enable to see asynchronous commands in a table view. Requires `run_async`.
- `simplify_branches = 0/1` - simplifies branch name in the branch view.

### Aliases
You can create your own aliases for commands. To create your own aliases, edit .mudsettings file, `[alias]` section. .mudsettings has the following aliases by default:
```ini
[alias]
to = git checkout
fetch = git fetch
pull = git pull
push = git push
```

## Labeling

You can modify your .mudconfig file by using following commands:

### Adding and labeling repositories
- `mud add <label> <path>` - adds path with an optional label.
- `mud add <path>` - adds path without a label.

### Removing labels and repositories
- `mud remove <label>` - removes label from all directories.
- `mud remove <path>` - removes directory with a specified path.
- `mud remove <label> <path>` - removes label from a directory.
