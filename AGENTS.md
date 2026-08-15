# AGENTS.md

## What mud does

`mud` is a CLI tool for running commands across multiple git repositories simultaneously.
You point it at a directory that contains a `.mudconfig` file and it dispatches any
command — native (`mud status`, `mud log`) or arbitrary shell (`mud git pull`) — to
every repo listed in that config, with optional filtering by label, branch, or
working-tree state.

## Module map

| File | Purpose |
|------|---------|
| `src/mud/__init__.py` | Entry point. Initialises settings, instantiates `App`, calls `run()`. |
| `src/mud/app.py` | CLI dispatch. Parses args, applies filters, calls the right `Runner` method. |
| `src/mud/runner.py` | All output and execution. Native display commands (`status`, `info`, `log`, …) and shell execution modes (`run_ordered`, `run_async`, `run_async_table_view`). |
| `src/mud/config.py` | `.mudconfig` I/O. Reads/writes the TSV config file; implements `init`, `add`, `remove`, `prune`. |
| `src/mud/settings.py` | `~/.config/mud/settings.ini` I/O. Reads and writes user preferences. |
| `src/mud/commands.py` | Constants for every command name and filter flag prefix. |
| `src/mud/styles.py` | ANSI escape codes and nerd-font glyphs. |
| `src/mud/utils.py` | Shared helpers: `PrettyTable` creation, error printing, the `configure` wizard. |

## Testing

Tests live in `tests/`. They are **external (black-box) CLI tests**: each test runs
`python -m mud <args>` as a real subprocess against git repos created in a temporary
directory, then checks the exit code and stdout.

This approach is right for `mud` because:
- The only interface a user has with `mud` is the CLI itself.
- Every meaningful state is reachable by setting up real git repos.
- No mocking needed — tests exercise exactly what a user experiences.

### Running tests locally

```sh
pip install -e ".[dev]"
pytest
```

### Test layout

| File | What it covers |
|------|----------------|
| `tests/helpers.py` | `make_git_repo()` and `run_mud()` — shared utilities used by every test file. |
| `tests/conftest.py` | pytest fixtures: `repos`, `repos_labeled`, `home`. |
| `tests/test_config.py` | `init`, `add`, `remove`, `prune` commands. |
| `tests/test_display.py` | `status`, `info`, `log`, `labels`, `branches`, `tags` commands. |
| `tests/test_run.py` | Shell command execution across all three run modes. |
| `tests/test_filters.py` | Filter flags: `-l=` (include label), `-L=` (exclude label), `-b=` (branch). |

### CI / publishing gates

Tests run automatically on every push and pull request via `.github/workflows/test.yaml`.

Publishing to PyPI and AUR is **blocked** until the test job passes — both publish
workflows declare `needs: [test]` and will not proceed if any test fails.
