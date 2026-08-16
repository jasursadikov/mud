# mud — Agent Instructions

## What mud does

`mud` runs git commands (and arbitrary shell commands) across multiple repositories simultaneously. It reads a `.mudconfig` TSV file listing repo paths and optional labels, then dispatches to every matching repo with filtering, async execution, and rich terminal output.

## Build and test

```sh
pip install -e ".[dev]"   # install with dev deps
python -m build           # build wheel
pytest                    # run tests (verbose by default)
pytest tests/test_run.py  # run a single file
```

## Entry point

`mud` CLI → `mud:run` in `src/mud/__init__.py` → `App` in `src/mud/app.py`

## Module map

| File | Purpose |
|---|---|
| `src/mud/__init__.py` | Entry point; initialises `Settings`, creates `App`, calls `run()` |
| `src/mud/app.py` | CLI dispatch; parses args, applies filters, calls `Runner` |
| `src/mud/runner.py` | All display commands and execution modes |
| `src/mud/config.py` | `.mudconfig` TSV read/write; `init`, `add`, `remove`, `prune` |
| `src/mud/settings.py` | `~/.config/mud/settings.ini` read/write |
| `src/mud/commands.py` | Constants for every command name and filter flag prefix |
| `src/mud/styles.py` | ANSI escape codes and Nerd Font glyphs |
| `src/mud/utils.py` | Shared helpers: table creation, error printing, configure wizard |

Full module details, architecture patterns, and error codes are in `.github/copilot-instructions.md`.

## Tests

Tests are black-box CLI tests — each runs `python -m mud` as a subprocess against real git repos in a temp directory. No mocking.

| File | Covers |
|---|---|
| `tests/test_config.py` | `init`, `add`, `remove`, `prune` |
| `tests/test_display.py` | `status`, `info`, `log`, `labels`, `branches`, `tags` |
| `tests/test_run.py` | Execution modes and flags |
| `tests/test_filters.py` | `-l=`, `-L=`, `-b=`, `-B=`, `-n=` filter flags |
| `tests/test_states.py` | Edge-case repo states (unborn, detached, rebasing) |

## Knowledge base update rule

After editing any file under `src/mud/`, update the affected sections of `.github/copilot-instructions.md` before finishing the task.

If user-facing behaviour changed (commands, flags, or settings), also update the relevant table rows in `README.md`. Table edits only — no new prose.
