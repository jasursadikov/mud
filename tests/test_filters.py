"""
Tests for filter flags: -l= (include label), -L= (exclude label), -b= (branch).

All shell commands here use -a to run in ordered mode so the output is
straightforward to assert on.
"""
import subprocess
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
