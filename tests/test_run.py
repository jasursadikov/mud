"""
Tests for shell command execution modes.

mud has three execution modes controlled by the -a (async) and -t (table) flags.
Default settings have both enabled, so:

  mud <cmd>        ->  async + table  (run_async_table_view)
  mud -t <cmd>     ->  async, no table  (run_async)
  mud -a <cmd>     ->  no async, no table  (run_ordered)  <- most readable output

We test that all modes exit 0 and that the command actually ran in each repo.
"""
from pathlib import Path
from helpers import run_mud


def test_run_ordered(repos: Path, home: Path):
	"""mud -a <cmd> runs sequentially, one repo at a time."""
	result = run_mud("-a", "echo", "hello", cwd=repos, home=home)
	assert result.returncode == 0
	assert "hello" in result.stdout


def test_run_async(repos: Path, home: Path):
	"""mud -t <cmd> runs all repos concurrently without the table view."""
	result = run_mud("-t", "echo", "hello", cwd=repos, home=home)
	assert result.returncode == 0
	assert "hello" in result.stdout


def test_run_async_table_view(repos: Path, home: Path):
	"""mud <cmd> uses the live table view by default."""
	result = run_mud("echo", "hello", cwd=repos, home=home)
	assert result.returncode == 0


def test_run_explicit_command_flag(repos: Path, home: Path):
	"""-c= lets you pass a command that contains spaces or special characters."""
	result = run_mud("-a", "-c=echo hello", cwd=repos, home=home)
	assert result.returncode == 0
	assert "hello" in result.stdout


def test_run_double_dash_separator(repos: Path, home: Path):
	"""mud -t -- <cmd> treats everything after -- as the literal command."""
	result = run_mud("-t", "--", "echo", "hello", cwd=repos, home=home)
	assert result.returncode == 0
	assert "hello" in result.stdout


def test_run_command_runs_in_every_repo(repos: Path, home: Path):
	"""The command is executed once per repo in the config."""
	result = run_mud("-a", "echo", "hello", cwd=repos, home=home)
	# "hello" appears at least once per repo (the header also echoes the command name)
	assert result.stdout.count("hello") >= 2
