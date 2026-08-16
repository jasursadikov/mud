"""
Tests for display commands against repos in unusual states.

mud must handle every state gracefully — exit 0, no crashes.
The six display commands are run against four edge-case repo states:

  no commits   — git init only, HEAD is unborn
  detached     — HEAD points at a commit hash, not a branch
  on tag       — HEAD detached at a tagged commit
  rebasing     — rebase stopped mid-way due to a conflict
"""
import pytest
from pathlib import Path
from helpers import (
	run_mud,
	make_empty_repo,
	make_detached_repo,
	make_tagged_repo,
	make_rebasing_repo,
)

DISPLAY_COMMANDS = ["status", "info", "log", "labels", "branches", "tags"]


# ---------------------------------------------------------------------------
# Fixtures — one per repo state
# ---------------------------------------------------------------------------

@pytest.fixture
def repo_no_commits(tmp_path: Path) -> Path:
	make_empty_repo(tmp_path / "repo_a")
	(tmp_path / ".mudconfig").write_text("repo_a\t\n")
	return tmp_path


@pytest.fixture
def repo_detached(tmp_path: Path) -> Path:
	make_detached_repo(tmp_path / "repo_a")
	(tmp_path / ".mudconfig").write_text("repo_a\t\n")
	return tmp_path


@pytest.fixture
def repo_on_tag(tmp_path: Path) -> Path:
	make_tagged_repo(tmp_path / "repo_a")
	(tmp_path / ".mudconfig").write_text("repo_a\t\n")
	return tmp_path


@pytest.fixture
def repo_rebasing(tmp_path: Path) -> Path:
	make_rebasing_repo(tmp_path / "repo_a")
	(tmp_path / ".mudconfig").write_text("repo_a\t\n")
	return tmp_path


# ---------------------------------------------------------------------------
# Tests — parametrised over every display command
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("cmd", DISPLAY_COMMANDS)
def test_display_no_commits(repo_no_commits: Path, home: Path, cmd: str):
	"""Display commands must not crash on a repo with no commits."""
	result = run_mud(cmd, cwd=repo_no_commits, home=home)
	assert result.returncode == 0


@pytest.mark.parametrize("cmd", DISPLAY_COMMANDS)
def test_display_detached_head(repo_detached: Path, home: Path, cmd: str):
	"""Display commands must not crash on a repo with detached HEAD."""
	result = run_mud(cmd, cwd=repo_detached, home=home)
	assert result.returncode == 0


@pytest.mark.parametrize("cmd", DISPLAY_COMMANDS)
def test_display_on_tag(repo_on_tag: Path, home: Path, cmd: str):
	"""Display commands must not crash on a repo checked out at a tag."""
	result = run_mud(cmd, cwd=repo_on_tag, home=home)
	assert result.returncode == 0


@pytest.mark.parametrize("cmd", DISPLAY_COMMANDS)
def test_display_rebasing(repo_rebasing: Path, home: Path, cmd: str):
	"""Display commands must not crash on a repo that is mid-rebase."""
	result = run_mud(cmd, cwd=repo_rebasing, home=home)
	assert result.returncode == 0
