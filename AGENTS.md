# AI Agent Instructions

## What `mud` does

`mud` runs git commands (and arbitrary shell commands) across multiple repositories simultaneously. It reads a `.mudconfig` TSV file listing repo paths and optional labels, then dispatches to every matching repo with filtering, async execution, and rich terminal output.

For commands, flags, and settings refer to `README.md` — it is the source of truth for user-facing behaviour. For runtime dependencies refer to `requirements.txt`.

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

## Architecture notes

**Global settings instance** — `utils.settings` is a single `Settings` object created in `__init__.run()` and accessed across all modules.

**Command dispatch** — `App.run()` routes to either a native `Runner` method (matched against constants in `commands.py`) or a shell pass-through. The `--` separator and `-c=<cmd>` flag both reach the shell path.

**Execution modes** — three modes controlled by `run_async` + `run_table` settings (toggled by `-a` / `-t` flags): sequential, async streamed, async live-table.

**Filter chain** — `App._filter_with_arguments()` applies up to eight filters in sequence (ignore label, include/exclude label, include/exclude branch, name substring, modified, diverged). Each step removes non-matching repos.

**Nerd Fonts** — every glyph in `styles.GLYPHS` has an ASCII fallback. `utils.glyphs(key)` selects between them based on the `nerd_fonts` setting, so mud works with or without a patched font.

## Tests

Tests are black-box CLI tests — each runs `python -m mud` as a subprocess against real git repos in a temporary directory.

| File | Covers |
|---|---|
| `tests/test_config.py` | `init`, `add`, `remove`, `prune` |
| `tests/test_display.py` | `status`, `info`, `log`, `labels`, `branches`, `tags` |
| `tests/test_run.py` | Execution modes and flags |
| `tests/test_filters.py` | `-l=`, `-L=`, `-b=`, `-B=`, `-n=` filter flags |
| `tests/test_states.py` | Edge-case repo states (unborn, detached, rebasing) |

## Knowledge base update rule
After editing any file under `src/mud/`, update the affected sections of this file before finishing the task.
`README.md` is the source of truth for user-facing behaviour — if commands, flags, or settings changed, update the relevant table rows there. Table edits only — no new prose.

# Git

## Branching
- All new features should have `feature/` prefix
- Bugfixes are using `bugfix/` prefix

## Tags
Tags format is vX.Y.Z
