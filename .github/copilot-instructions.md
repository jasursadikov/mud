# mud — Codebase Knowledge Base

## Project overview

`mud` (`mud-git` on PyPI/AUR) runs git commands and arbitrary shell commands across multiple repositories simultaneously. It reads a `.mudconfig` TSV file, applies filters, and dispatches to every matching repo with async execution and rich terminal output.

- **Entry point:** `mud` CLI → `mud:run` → `App.run()`
- **Python:** >= 3.13
- **Runtime deps:** `prettytable`, `pygit2`
- **Build:** `setuptools` + `setuptools-scm` (version from git tags)
- **Install:** `pip install mud-git` or `paru -S mud-git`

---

## Project structure

```
src/mud/
├── __init__.py      # run() — entry point; sets utils.settings
├── __main__.py      # enables python -m mud
├── app.py           # App class — CLI dispatch and filter chain
├── commands.py      # all command name and filter flag constants
├── config.py        # Config class — .mudconfig read/write/management
├── runner.py        # Runner class — display commands and execution modes
├── settings.py      # Settings class — settings.ini read/write
├── styles.py        # ANSI escape codes + Nerd Font glyph dict
└── utils.py         # shared helpers, table creation, error codes

tests/
├── conftest.py      # fixtures: home, repos, repos_labeled
├── helpers.py       # repo factories + run_mud() subprocess runner
├── test_config.py   # init, add, remove, prune
├── test_display.py  # status, info, log, labels, branches, tags
├── test_filters.py  # -l=, -L=, -b=, -B=, -n= flags
├── test_run.py      # execution modes and flags
└── test_states.py   # edge-case states: unborn, detached, rebasing
```

---

## Module dependency graph

```
__init__.py  →  App (app.py)
                  ├── commands.py   (constants only)
                  ├── Config (config.py)  →  utils
                  └── Runner (runner.py)  →  utils, styles, pygit2

utils.py     →  Settings (settings.py), styles.py, prettytable
styles.py    →  (no imports — pure constants)
commands.py  →  (no imports — pure constants)
```

`utils.settings` is the single shared `Settings` instance, set by `__init__.run()` and accessed across all modules.

---

## Key architectural patterns

### Command dispatch (app.py)
Two paths in `App.run()`:
- **Native commands** — matched against `COMMANDS` constant lists → `Runner` methods
- **Shell pass-through** — everything else assembled as a string → `Runner.run_*`

`--` separator and `-c=<cmd>` / `--command=<cmd>` both route to shell pass-through.

### Three execution modes
Controlled by `run_async` + `run_table` settings (toggled by `-a` / `-t` flags):

| `run_async` | `run_table` | Mode |
|---|---|---|
| False | any | `Runner.run_ordered()` — sequential subprocess |
| True | False | `Runner.run_async()` — asyncio.gather, streamed output |
| True | True | `Runner.run_async_table_view()` — live-updating table |

### Filter chain (`App._filter_with_arguments()`)
Applied in order; each step removes non-matching repos:
1. Always exclude repos with label `ignore`
2. `--label` / `-l=` — include by label
3. `--not-label` / `-L=` — exclude by label
4. `--branch` / `-b=` — include by current branch
5. `--not-branch` / `-B=` — exclude by current branch
6. `--name` / `-n=` — include by path substring
7. `--modified` / `-m` — include only repos with dirty working tree
8. `--diverged` / `-d` — include only repos ahead/behind upstream

### Nerd Fonts duality
`styles.GLYPHS` maps every key to `[nerd_font_char, ascii_fallback]`. `utils.glyphs(key)` picks index 0 or 1 based on `nerd_fonts` setting.

### Live table refresh
`Runner.run_async_table_view` redraws in-place using `\033[A\033[K` (cursor-up + clear-line) per previously printed line.

---

## `.mudconfig` file format

Tab-separated values, one repo per line:
```
<path>\t<comma_separated_labels>
```
Paths may be relative (to config file location) or absolute (`~` expanded).

`Config.find()` walks up from CWD; falls back to `settings.mud_settings['config_path']` (global config set by `mud set-global`).

---

## Settings

Stored at `~/.config/mud/settings.ini` (legacy: `~/.mudsettings`). Accessed via `utils.settings`.

| Key | Default | Description |
|---|---|---|
| `nerd_fonts` | `True` | Use Nerd Font glyphs |
| `run_async` | `True` | Run commands in parallel |
| `run_table` | `True` | Show live table view (requires `run_async`) |
| `display_header` | `True` | Show table column headers |
| `display_borders` | `True` | Show table borders |
| `round_corners` | `False` | Round vs. square table corners |
| `display_absolute_paths` | `False` | Show absolute paths |
| `config_path` | `''` | Global fallback `.mudconfig` path |

Default aliases: `fetch = git fetch`, `pull = git pull`, `push = git push`.

---

## commands.py constants

All command constants are **lists of strings** (supporting aliases):

| Constant | Values |
|---|---|
| `ADD` | `['add', 'a']` |
| `REMOVE` | `['remove', 'rm']` |
| `PRUNE` | `['prune']` |
| `LOG` | `['log', 'l']` |
| `INFO` | `['info', 'i']` |
| `INIT` | `['init']` |
| `TAGS` | `['tags', 'tag', 't']` |
| `LABELS` | `['labels', 'lb']` |
| `STATUS` | `['status', 'st']` |
| `BRANCHES` | `['branch', 'branches', 'br']` |
| `REMOTE_BRANCHES` | `['remote-branch', 'remote-branches', 'rbr']` |
| `COMPLETE_BRANCH` | `['complete-branch']` |
| `COMPLETE_BRANCH_ALL` | `['complete-branch-all']` |
| `CONFIGURE` | `['configure', 'config']` |
| `GET_CONFIG` | `['get-config']` |
| `SET_GLOBAL` | `['set-global']` |
| `COMMANDS` | union of all above |

Filter flag constants are **tuples**: e.g. `LABEL_PREFIX = '-l=', '--label='`.

---

## runner.py — Runner class

### Display methods (all receive `repos: dict[str, list[str]]`)

| Method | Table columns |
|---|---|
| `info(repos)` | Directory, Url, Commits, User Commits, Size, Labels |
| `status(repos)` | Directory, Branch, Origin Sync, Stash, Status, Modified Files |
| `labels(repos)` | Directory, Labels |
| `log(repos)` | Directory, Branch, Hash, Author, Time, Message |
| `branches(paths, remote)` | Directory, Branches |
| `tags(repos)` | Directory, Tags |
| `complete_branches(paths, include_remote)` | prints names for shell completion |

### Key static helpers

| Method | Purpose |
|---|---|
| `_get_head_info(repo)` | Colored branch/tag/hash string; handles unborn, detached, normal |
| `_get_origin_sync(repo)` | Ahead/behind counts vs. upstream |
| `_get_status_string(files)` | Compact string e.g. `"2 + 1 * 1 -"` from FileStatus flags |
| `_get_formatted_path(path, ...)` | DIM prefix components, normal final segment |
| `_get_branch_icon(prefix)` | Nerd Font glyph by branch naming convention |

---

## config.py — Config class

| Method | Purpose |
|---|---|
| `Config.find()` | Static; walks CWD up for `.mudconfig`, falls back to global |
| `load(file_path)` | Reads TSV into `self.data: dict[str, list[str]]` |
| `save(file_path)` | Writes TSV; validates labels with `r'^\w+$'` |
| `init()` | Discovers repos recursively by finding `.git` dirs |
| `add(path, label)` | Adds path + optional label |
| `remove(label, path)` | Dispatches to `remove_path` or `remove_label` |
| `prune()` | Removes entries where path no longer exists on disk |
| `filter_label(label, repos)` | Returns repos filtered to those with the given label |

---

## utils.py — key items

| Item | Purpose |
|---|---|
| `settings: Settings` | Module-level global; set by `__init__.run()` |
| `CONFIG_FILE_NAME` | `'.mudconfig'` |
| `SETTINGS_FILE_NAME` | `'settings.ini'` |
| `glyphs(key)` | Returns nerd font or ASCII fallback based on settings |
| `get_table(field_names)` | Creates `PrettyTable` respecting borders/corners/headers settings |
| `print_table(table)` | Removes empty columns, wraps at terminal width |
| `link(text, url)` | Returns OSC 8 hyperlink string |
| `print_error(code, exit, meta)` | Prints formatted error; optionally calls `sys.exit` |

---

## Error codes

| Code | Meaning |
|---|---|
| 0 | Stopped by user (KeyboardInterrupt) |
| 1 | No repositories matching filter |
| 2 | Invalid command |
| 3 | No git repos found in directory |
| 4 | Invalid input |
| 5 | `.mudconfig` not found |
| 6 | Item not found in `.mudconfig` |
| 7 | Invalid path |
| 8 | `.git` directory not found at path |
| 9 | Repo in `.mudconfig` but directory missing on disk |

---

## Test infrastructure

Tests are **black-box CLI tests** — no mocking. Each test runs `python -m mud` as a subprocess against real git repos in a temp directory.

### `tests/helpers.py` — repo factories

| Function | State created |
|---|---|
| `make_git_repo(path)` | Normal repo with one commit |
| `make_empty_repo(path)` | Init only — unborn HEAD |
| `make_detached_repo(path)` | HEAD detached at commit hash |
| `make_tagged_repo(path)` | HEAD detached at tag `v1.0` |
| `make_rebasing_repo(path)` | Mid-rebase due to conflict |
| `run_mud(*args, cwd, home)` | Runs `python -m mud` with isolated `HOME` |

### `tests/conftest.py` — fixtures

| Fixture | Provides |
|---|---|
| `home` | Isolated home directory |
| `repos` | `repo_a` + `repo_b` with `.mudconfig` |
| `repos_labeled` | Same with `label_a` / `label_b` |

---

## CI / publishing

| Workflow | Trigger | What it does |
|---|---|---|
| `test.yaml` | Push / PR | Python 3.13, build wheel, `pytest -v` |
| `publish-pypi.yaml` | Release published | Tests → `pypa/gh-action-pypi-publish` |
| `publish-aur.yaml` | Release published | Tests → update `PKGBUILD` → deploy to AUR |

Publishing to PyPI and AUR requires `needs: [test]` — blocked if tests fail.
