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

## Binary releases and AUR

`.github/workflows/publish-aur.yaml` builds stable `vX.Y.Z` releases, with an explicit published tag required for manual runs. It checks out that exact tag, tests the wheel, freezes an x86_64 executable with PyInstaller on Ubuntu 22.04, and reruns the CLI tests against the executable. Build tools are pinned in `.github/requirements-binary.txt`.

`.github/pyinstaller/runtime_tls.py` selects a system CA bundle before pygit2 is imported when the bundled Python's compiled-in certificate paths are absent on the target distribution. Explicit `SSL_CERT_FILE` and `SSL_CERT_DIR` overrides are preserved. The Arch package depends on `ca-certificates`, and its smoke test clears those overrides to verify automatic discovery.

The workflow fills `@VERSION@` and `@SHA256@` in the root `PKGBUILD` template, tests the package in Arch Linux, uploads `mud-X.Y.Z-linux-x86_64.tar.gz` to the release, then publishes `mud` and generated `.SRCINFO` to AUR using `AUR_USERNAME`, `AUR_EMAIL`, and `AUR_SSH_KEY`. Published assets are immutable; retry failed jobs with the original artifact. The package installs the bundled runtime under `/opt/mud` and links `/usr/bin/mud`, with no end-user Python build. `mud-git` is a provided/conflicting legacy AUR package; its listing is retired by requesting an AUR merge after `mud` is published. The PyPI distribution is still named `mud-git`.

## Entry point

`mud` CLI → `mud:run` in `src/mud/__init__.py` → `App` in `src/mud/app.py`; `mud completion` is dispatched to `completion.complete()` before writable settings are initialised.

## Module map

| File | Purpose |
|---|---|
| `src/mud/__init__.py` | Entry point; creates `App`, dispatches completion or initialises `Settings` and calls `run()` |
| `src/mud/app.py` | CLI dispatch; parses args, applies filters, calls `Runner` |
| `src/mud/completion.py` | Exports the Carapace spec and provides read-only dynamic completion via `C_ARG<n>` / `C_VALUE` |
| `src/mud/runner.py` | All display commands and execution modes |
| `src/mud/config.py` | `.mudconfig` TSV read/write; `init`, `add`, `remove`, `prune` |
| `src/mud/settings.py` | `~/.config/mud/settings.ini` read/write; legacy settings migration; read-only initialisation for completion |
| `src/mud/commands.py` | Constants for every command name and filter flag prefix |
| `src/mud/styles.py` | ANSI escape codes and Nerd Font glyphs |
| `src/mud/utils.py` | Shared helpers: table creation, error printing, configure wizard, help banner (independent of source-file paths for frozen builds) |

## Architecture notes

**Global settings instance** — `utils.settings` is a single `Settings` object created in `__init__.run()` and accessed across all modules.

**Settings location** — All settings writes target `~/.config/mud/settings.ini`; mud never creates `~/.mudsettings`. An existing modern file takes precedence and leaves the legacy file untouched; otherwise normal startup moves the legacy file to the modern location, preserving its contents, or creates defaults at the modern location if neither file exists. The legacy file is removed only after a successful move. Completion can read legacy settings as a fallback but never migrates them. Ordinary package imports and builds do not initialise settings.

**Command dispatch** — `App.run()` routes to either a native `Runner` method (matched against constants in `commands.py`) or a shell pass-through. The `--` separator and `-c=<cmd>` flag both reach the shell path.

**Carapace completion** — `mud completion carapace` exports a shell-independent spec; its fixed `mud completion values` callback handles mud's equals-only flags without executing user input. Command/flag descriptions come from the argparse definitions, aliases from settings, and label/path/branch values from the discovered config. Local and remote branch names reuse `Runner._get_unique_branch_names()`. Nothing is completed after `--`, inside `-c=`, or in arbitrary shell/alias arguments. Filters remain available after a completed `-c=` token. Neither spec export nor completion creates settings files.

**Argument metadata** — argparse registers value-taking options without trailing `=` and toggles as booleans, so empty values and `-t` cannot consume native commands. The execution scanner still requires `-flag=value`; completion inserts the equals sign.

**Execution modes** — three modes controlled by `run_async` + `run_table` settings (toggled by `-a` / `-t` flags): sequential, async streamed, async live-table.

**Frozen subprocesses** — `Runner` restores the original `LD_LIBRARY_PATH` (or removes it if originally unset) in the child-command environment when running under PyInstaller, so Git and arbitrary shell commands use system libraries rather than the bundled runtime.

**Filter chain** — `App._filter_with_arguments()` applies up to nine filters in sequence (ignore label, include/exclude label, include/exclude branch, include/exclude name substring, modified, diverged). Each step removes non-matching repos. Repeated `-N=` / `--not-name=` values exclude any matching path substring; empty exclusions are ignored.

**Nerd Fonts** — every glyph in `styles.GLYPHS` has an ASCII fallback. `utils.glyphs(key)` selects between them based on the `nerd_fonts` setting, so mud works with or without a patched font.

## Tests

Tests are black-box CLI tests — each runs `python -m mud` as a subprocess against real git repos in a temporary directory. Set `MUD_EXECUTABLE` to an absolute executable path to run CLI and completion tests against a frozen binary instead; import-only checks still use the Python environment.

| File | Covers |
|---|---|
| `tests/test_config.py` | `init`, `add`, `remove`, `prune` |
| `tests/test_settings.py` | Import side effects, first-launch settings location, legacy moves and migration failures, modern-file precedence, and settings save destination |
| `tests/test_display.py` | `status`, `info`, `log`, `labels`, `branches`, `tags` |
| `tests/test_run.py` | Execution modes, flags, and preservation of the external-command library path in frozen builds |
| `tests/test_filters.py` | `-l=`, `-L=`, `-b=`, `-B=`, `-n=`, `-N=` filter flags and native-command parsing regressions |
| `tests/test_completion.py` | Completion callback, dynamic values, command boundaries, read-only settings precedence/discovery, and optional real Carapace/Nushell integration |
| `tests/test_states.py` | Edge-case repo states (unborn, detached, rebasing) |

Carapace integration tests run when `carapace` is on `PATH`; the Nushell round-trip test also requires `nu`. Tests isolate `HOME`, Carapace config/cache directories, and use `MUD_EXECUTABLE` or the current Python environment's `mud` executable.

## Knowledge base update rule
After editing any file under `src/mud/`, update the affected sections of this file before finishing the task.
`README.md` is the source of truth for user-facing behaviour — if commands, flags, or settings changed, update the relevant table rows there. Table edits only — no new prose.

# Git

## Branching
- All new features should have `feature/` prefix
- Bugfixes are using `bugfix/` prefix

## Tags
Tags format is vX.Y.Z
