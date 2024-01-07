# mud

![Demo](img.png)

mud is a multidirectory git runner. Using this tool you can run git commands in a groups of repositories. This tool is not limited to git commands only, you can run any commands as you wish, but this tool was primarally designed to be used with git, so each referenced directory should have `.git`.

## Getting started

To get using `mud`, run `mud init` command to create `.mudconfig` file. This file is important to keep references to repositories. All repositories in current dictionary would be included to `.mudconfig`.

### Adding repositories
- `mud add label path/` - adds path with an optional label.
- `mud add path/` - adds path without a label.

### Removing repositories
- `mud remove label` - removes label from all directories.
- `mud remove path/` - removes directory with a specified path.
- `mud remove label path/` - removes label from a directory.

All entries are stored in `.mudconfig` in XML format. After making your first entry, you can open `.mudconfig` in a text editor and modify it according to your needs.

### Global .mudconfig
- `mud --set-global` - sets current `.mudconfig` as a global configuration, so it would be used as a fallback configuration to run from any directory.

## Using

### Commands
- `mud <COMMAND>` will run command on all repositories. To filter repositories check [filtering](###filtering) section.

### Info
- `mud status` - displays status in a compact table for multiple repositories.
- `mud log` - displays log with information about repo's last commit, it's time and it's author.
- `mud branch` - displays all branches in repositories.

### Filters
mud has following filters:
- `-l=<label>` or `--label=<label>` - filters out repositories by mud labels.
- `-b=<branch>` or `--branch=<branch>` - filters out repositories by current branch name.
- `-m` or `--modified` - filters out modified repostories.
- `-d` or `--diverged` - filters repositories with diverged branches.

All filters should be applied before the command. 

```
Example:
mud -b=master -d git pull
# Filters out all repos with master branch and diverged branches and then runs pull command
```

## Settings

Settings are stored in your home directory in `.mudsettings` file.

- `config_path = /home/user/path/.mudconfig` - this is set up by `mud --set-global` command
- `nerd_fonts = 0/1` - toggles whenever nerd font icons should be used in output. Affects `mud status` and `mud log` commands.
- `auto_fetch = 0/1` - when enabled, `mud status` and `mud log` do fetch for all repos when invoked.
- `run_async = 0/1` - affect general commands. When enabled, commands do run asyncronously and then print result when finished.
- `run_table = 0/1` - when enabled, commands output are displayed in the table with last message provided. Requires `run_async`.
- `simplify_branches = 0/1` - will simplify branch names in `mud branch` command, so folders will have only first character of the name

### Aliases
You can create your own aliases for commands. To create your own aliases, edit .mudsettings file, `[alias]` section. .mudsettings has following aliases by default:
```ini
[alias]
to = git checkout
fetch = git fetch
pull = git pull
push = git push
```
