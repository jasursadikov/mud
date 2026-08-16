"""
Tests for read-only display commands: status, info, log, labels, branches, tags.

Each command should exit 0 and include the repo directory names in its output.
Output contains ANSI colour codes but plain text like "repo_a" is always present.
"""
from pathlib import Path
from helpers import run_mud


def test_no_args_shows_help(tmp_path: Path, home: Path):
	"""mud with no arguments must print help without raising an exception (issue #90).

	This crashed on Python 3.12 with an AssertionError inside argparse._format_usage
	because the auto-generated usage string was too long and triggered a buggy
	regex-based wrapping assertion.  The fix is to supply a custom usage= string
	to ArgumentParser so that assertion is never reached.
	"""
	result = run_mud(cwd=tmp_path, home=home)
	assert result.returncode == 0, f"mud with no args exited {result.returncode}:\n{result.stderr}"
	# Should mention key commands in the help output
	assert "mud" in result.stdout or "mud" in result.stderr


def test_status(repos: Path, home: Path):
	result = run_mud("status", cwd=repos, home=home)
	assert result.returncode == 0
	assert "repo_a" in result.stdout
	assert "repo_b" in result.stdout


def test_info(repos: Path, home: Path):
	result = run_mud("info", cwd=repos, home=home)
	assert result.returncode == 0
	assert "repo_a" in result.stdout
	assert "repo_b" in result.stdout


def test_log(repos: Path, home: Path):
	result = run_mud("log", cwd=repos, home=home)
	assert result.returncode == 0
	assert "repo_a" in result.stdout
	assert "repo_b" in result.stdout


def test_labels(repos: Path, home: Path):
	result = run_mud("labels", cwd=repos, home=home)
	assert result.returncode == 0
	assert "repo_a" in result.stdout
	assert "repo_b" in result.stdout


def test_labels_shows_label_values(repos_labeled: Path, home: Path):
	result = run_mud("labels", cwd=repos_labeled, home=home)
	assert result.returncode == 0
	assert "label_a" in result.stdout
	assert "label_b" in result.stdout


def test_branches(repos: Path, home: Path):
	result = run_mud("branches", cwd=repos, home=home)
	assert result.returncode == 0
	assert "repo_a" in result.stdout
	assert "repo_b" in result.stdout


def test_tags(repos: Path, home: Path):
	result = run_mud("tags", cwd=repos, home=home)
	assert result.returncode == 0
	assert "repo_a" in result.stdout
	assert "repo_b" in result.stdout
