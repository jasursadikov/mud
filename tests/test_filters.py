"""
Tests for filter flags: -l= (include label), -L= (exclude label), -b= (branch).

All shell commands here use -a to run in ordered mode so the output is
straightforward to assert on.
"""
import subprocess
import pytest
from pathlib import Path
from helpers import run_mud


# ---------------------------------------------------------------------------
# Label filters
# ---------------------------------------------------------------------------

def test_label_include_filter(repos_labeled: Path, home: Path):
	"""-l=<label> restricts execution to repos that carry that label."""
	result = run_mud("-a", "-l=label_a", "echo", "hello", cwd=repos_labeled, home=home)
	assert result.returncode == 0
	assert "repo_a" in result.stdout
	assert "repo_b" not in result.stdout


def test_label_exclude_filter(repos_labeled: Path, home: Path):
	"""-L=<label> skips repos that carry that label."""
	result = run_mud("-a", "-L=label_a", "echo", "hello", cwd=repos_labeled, home=home)
	assert result.returncode == 0
	assert "repo_b" in result.stdout
	assert "repo_a" not in result.stdout


# ---------------------------------------------------------------------------
# Branch filter
# ---------------------------------------------------------------------------

def test_name_filter(repos: Path, home: Path):
	"""-n=<string> restricts execution to repos whose path contains that string."""
	result = run_mud("-a", "-n=repo_a", "echo", "hello", cwd=repos, home=home)
	assert result.returncode == 0
	assert "repo_a" in result.stdout
	assert "repo_b" not in result.stdout


@pytest.mark.parametrize("command", [
	("status",),
	("echo", "hello"),
	("--", "echo", "hello"),
	("-c=echo hello",),
], ids=["native", "passthrough", "separator", "explicit-command"])
@pytest.mark.parametrize("filters, expected", [
	(("-N=po_a",), ("repo_b",)),
	(("--not-name=po_b",), ("repo_a",)),
	(("-N=po_a", "-N=po_b"), ()),
	(("--not-name=po_a", "--not-name=po_b"), ()),
	(("-N=po_a", "--not-name=po_b"), ()),
	(("-n=repo", "-N=po_a"), ("repo_b",)),
	(("--name=repo", "--not-name=po_b"), ("repo_a",)),
	(("-n=po_a", "-N=po_a"), ()),
	(("-N=missing",), ("repo_a", "repo_b")),
	(("--not-name=PO_A",), ("repo_a", "repo_b")),
	(("-N=",), ("repo_a", "repo_b")),
	(("-N=", "-N=repo_a"), ("repo_b",)),
])
def test_name_exclude_filter(repos: Path, home: Path, command, filters, expected):
	result = run_mud("-a", *filters, *command, cwd=repos, home=home)
	assert result.returncode == 0, result.stderr
	for name in ("repo_a", "repo_b"):
		assert (name in result.stdout) == (name in expected), result.stdout


@pytest.mark.parametrize('flag', ['-t', '--table', '-n=', '-N=', '-l=', '-L=', '-b=', '-B='])
def test_flags_do_not_consume_native_command(repos: Path, home: Path, flag):
	result = run_mud(flag, 'status', cwd=repos, home=home)
	assert result.returncode == 0, result.stderr
	assert 'repo_a' in result.stdout
	assert 'repo_b' in result.stdout


def test_branch_filter(repos_labeled: Path, home: Path):
	"""-b=<branch> restricts execution to repos currently on that branch."""
	# Put repo_a on a feature branch; repo_b stays on the default branch.
	subprocess.run(
		["git", "checkout", "-b", "feature"],
		cwd=repos_labeled / "repo_a",
		check=True,
		capture_output=True,
	)

	result = run_mud("-a", "-b=feature", "echo", "hello", cwd=repos_labeled, home=home)
	assert result.returncode == 0
	assert "repo_a" in result.stdout
	assert "repo_b" not in result.stdout
